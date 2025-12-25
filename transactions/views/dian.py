# transactions/views/dian.py
"""
Vistas para procesamiento de facturas DIAN.
"""

from .base import *
from pathlib import Path
import pandas as pd
import zipfile
import rarfile

from .classification import clasificar_gasto_inteligente


@api_view(['POST'])
@permission_classes([IsAuthenticated, HasValidLicense])
def procesar_facturas_dian_excel(request):
    """
    Procesa archivos Excel de la DIAN.

    Archivos soportados:
    - Facturas_Recibidas_YYYYMM.xlsx (GASTOS)
    - Facturas_Emitidas_YYYYMM.xlsx (INGRESOS)
    """
    archivo = request.FILES.get('archivo')
    company_id = request.data.get('company')
    tipo = request.data.get('tipo')  # 'recibidas' o 'emitidas'

    if not archivo:
        return Response({'error': 'Debe subir un archivo'}, status=400)

    if not company_id:
        return Response({'error': 'Debe seleccionar una empresa'}, status=400)

    try:
        df = pd.read_excel(archivo)
        df.columns = df.columns.str.strip().str.lower()

        resultados = {
            'procesados': 0,
            'exitosos': 0,
            'errores': 0,
            'duplicados': 0,
            'detalles': []
        }

        for index, row in df.iterrows():
            resultados['procesados'] += 1

            try:
                if tipo == 'recibidas':
                    resultado = _crear_asiento_gasto_desde_dian(row, company_id)
                else:
                    resultado = _crear_asiento_ingreso_desde_dian(row, company_id)

                if resultado['estado'] == 'exitoso':
                    resultados['exitosos'] += 1
                elif resultado['estado'] == 'duplicado':
                    resultados['duplicados'] += 1
                else:
                    resultados['errores'] += 1

                resultados['detalles'].append(resultado)

            except Exception as e:
                resultados['errores'] += 1
                resultados['detalles'].append({
                    'fila': index + 2,
                    'estado': 'error',
                    'mensaje': str(e)
                })
                logger.error(f"Error procesando fila {index}: {str(e)}")

        return Response(resultados)

    except Exception as e:
        logger.error(f"Error general procesando Excel: {str(e)}")
        return Response({'error': str(e)}, status=500)


def _crear_asiento_gasto_desde_dian(row, company_id):
    """Crea asiento contable de GASTO desde factura recibida."""
    try:
        nit = str(row.get('nit proveedor') or row.get('nit emisor') or row.get('nit') or '').strip()
        nombre = str(
            row.get('razón social proveedor') or row.get('nombre emisor') or
            row.get('razón social') or row.get('razon social proveedor') or
            row.get('razon social') or ''
        ).strip()
        numero_factura = str(
            row.get('número de factura') or row.get('número documento') or
            row.get('numero de factura') or row.get('numero documento') or
            row.get('numero') or ''
        ).strip()

        fecha = _parsear_fecha_dian(row)
        valor = float(
            row.get('valor total') or row.get('total factura') or
            row.get('total') or row.get('valor') or 0
        )
        concepto = str(
            row.get('concepto') or row.get('descripción') or
            row.get('descripcion') or row.get('observaciones') or 'Gasto general'
        ).strip()

        if not nit or not valor or valor <= 0:
            return {
                'factura': numero_factura or 'N/A',
                'estado': 'error',
                'mensaje': 'Datos incompletos o valor inválido'
            }

        if _verificar_factura_duplicada(numero_factura, nit, company_id):
            return {
                'factura': numero_factura,
                'estado': 'duplicado',
                'mensaje': 'Factura ya registrada'
            }

        tercero = _obtener_o_crear_tercero(nit, nombre)

        cuenta_gasto_code, es_anomalia, razon_clasificacion = clasificar_gasto_inteligente(
            nit, nombre, valor, company_id
        )
        cuenta_gasto = Account.objects.get(code=cuenta_gasto_code)
        cuenta_caja = Account.objects.get(code='1105')

        with db_transaction.atomic():
            transaction = Transaction.objects.create(
                company_id=company_id,
                date=fecha,
                concept=f"Factura {numero_factura}: {concepto[:100]}",
                additional_description=f"Procesado automáticamente desde Excel DIAN - {nombre}"
            )

            Movement.objects.create(
                transaction=transaction,
                account=cuenta_gasto,
                third_party=tercero,
                debit=Decimal(str(valor)),
                credit=Decimal('0'),
                description=f"Factura {numero_factura}"
            )

            Movement.objects.create(
                transaction=transaction,
                account=cuenta_caja,
                third_party=tercero,
                debit=Decimal('0'),
                credit=Decimal(str(valor)),
                description=f"Pago factura {numero_factura}"
            )

        return {
            'factura': numero_factura,
            'estado': 'exitoso',
            'transaccion_id': transaction.id,
            'tercero': nombre,
            'valor': valor,
            'cuenta': cuenta_gasto_code
        }

    except Exception as e:
        return {
            'factura': numero_factura if 'numero_factura' in locals() else 'N/A',
            'estado': 'error',
            'mensaje': str(e)
        }


def _crear_asiento_ingreso_desde_dian(row, company_id):
    """Crea asiento contable de INGRESO desde factura emitida."""
    try:
        nit = str(row.get('nit adquiriente') or row.get('nit cliente') or row.get('nit') or '').strip()
        nombre = str(
            row.get('razón social adquiriente') or row.get('nombre cliente') or
            row.get('razón social') or row.get('razon social adquiriente') or
            row.get('razon social') or ''
        ).strip()
        numero_factura = str(
            row.get('número de factura') or row.get('número documento') or
            row.get('numero de factura') or row.get('numero') or ''
        ).strip()

        fecha_str = row.get('fecha') or row.get('fecha factura') or row.get('fecha emision')
        if pd.isna(fecha_str):
            fecha = date.today()
        else:
            fecha = pd.to_datetime(fecha_str)

        valor = float(row.get('valor total') or row.get('total factura') or row.get('total') or 0)
        concepto = str(row.get('concepto') or row.get('descripción') or row.get('descripcion') or 'Venta').strip()

        if not nit or not valor or valor <= 0:
            return {
                'factura': numero_factura or 'N/A',
                'estado': 'error',
                'mensaje': 'Datos incompletos'
            }

        if _verificar_factura_duplicada(numero_factura, nit, company_id):
            return {
                'factura': numero_factura,
                'estado': 'duplicado',
                'mensaje': 'Factura ya registrada'
            }

        tercero = _obtener_o_crear_tercero(nit, nombre)

        cuenta_ingreso = Account.objects.get(code='4135')
        cuenta_caja = Account.objects.get(code='1105')

        with db_transaction.atomic():
            transaction = Transaction.objects.create(
                company_id=company_id,
                date=fecha,
                concept=f"Factura venta {numero_factura}: {concepto[:100]}",
                additional_description=f"Procesado automáticamente desde Excel DIAN - {nombre}"
            )

            Movement.objects.create(
                transaction=transaction,
                account=cuenta_caja,
                third_party=tercero,
                debit=Decimal(str(valor)),
                credit=Decimal('0'),
                description=f"Cobro factura {numero_factura}"
            )

            Movement.objects.create(
                transaction=transaction,
                account=cuenta_ingreso,
                third_party=tercero,
                debit=Decimal('0'),
                credit=Decimal(str(valor)),
                description=f"Venta factura {numero_factura}"
            )

        return {
            'factura': numero_factura,
            'estado': 'exitoso',
            'transaccion_id': transaction.id,
            'tercero': nombre,
            'valor': valor
        }

    except Exception as e:
        return {
            'factura': numero_factura if 'numero_factura' in locals() else 'N/A',
            'estado': 'error',
            'mensaje': str(e)
        }


def _parsear_fecha_dian(row):
    """Parsea la fecha desde un row del Excel DIAN."""
    fecha_str = (
        row.get('fecha emisión') or
        row.get('fecha emision') or
        row.get('fecha recepción') or
        row.get('fecha recepcion') or
        row.get('fecha') or
        row.get('fecha factura')
    )

    if pd.isna(fecha_str):
        return date.today()

    try:
        if isinstance(fecha_str, str):
            fecha_limpia = fecha_str.strip()
            for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y']:
                try:
                    return datetime.strptime(fecha_limpia, fmt).date()
                except ValueError:
                    continue

            fecha_parsed = pd.to_datetime(fecha_str, dayfirst=True)
            return date(fecha_parsed.year, fecha_parsed.month, fecha_parsed.day)
        else:
            fecha_parsed = pd.to_datetime(fecha_str, dayfirst=True)
            return date(fecha_parsed.year, fecha_parsed.month, fecha_parsed.day)
    except Exception as e:
        logger.warning(f"Error parseando fecha '{fecha_str}': {e}")
        return date.today()


def _verificar_factura_duplicada(numero_factura, nit, company_id):
    """Verifica si la factura ya fue registrada."""
    if not numero_factura:
        return False

    return Transaction.objects.filter(
        company_id=company_id,
        concept__icontains=numero_factura
    ).exists()


def _obtener_o_crear_tercero(nit, nombre):
    """Crea tercero si no existe."""
    nit_limpio = re.sub(r'[^\d]', '', str(nit))

    if not nit_limpio:
        nit_limpio = '000000000'

    if not nombre:
        nombre = f"Tercero {nit_limpio}"

    tercero, created = ThirdParty.objects.get_or_create(
        nit=nit_limpio,
        defaults={'name': nombre}
    )

    if not created and tercero.name != nombre and nombre != f"Tercero {nit_limpio}":
        tercero.name = nombre
        tercero.save()

    return tercero


@api_view(['POST'])
@permission_classes([IsAuthenticated, HasValidLicense])
def procesar_archivo_comprimido(request):
    """
    Descomprime y procesa ZIP/RAR.
    Útil si recibes facturas individuales comprimidas.
    """
    archivo = request.FILES.get('archivo')
    company_id = request.data.get('company')

    if not archivo:
        return Response({'error': 'Debe subir un archivo'}, status=400)

    temp_dir = Path('temp_facturas')
    temp_dir.mkdir(exist_ok=True)

    archivo_path = temp_dir / archivo.name
    with open(archivo_path, 'wb+') as destination:
        for chunk in archivo.chunks():
            destination.write(chunk)

    try:
        if archivo.name.endswith('.zip'):
            with zipfile.ZipFile(archivo_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        elif archivo.name.endswith('.rar'):
            with rarfile.RarFile(archivo_path, 'r') as rar_ref:
                rar_ref.extractall(temp_dir)
        else:
            return Response({'error': 'Formato no soportado. Use ZIP o RAR'}, status=400)

        resultados = {
            'procesados': 0,
            'archivos_encontrados': [],
            'mensaje': 'Archivos descomprimidos exitosamente'
        }

        for file in temp_dir.rglob('*'):
            if file.is_file():
                resultados['archivos_encontrados'].append(str(file.name))
                resultados['procesados'] += 1

        import shutil
        shutil.rmtree(temp_dir)

        return Response(resultados)

    except Exception as e:
        logger.error(f"Error procesando archivo comprimido: {str(e)}")

        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        return Response({'error': str(e)}, status=500)
