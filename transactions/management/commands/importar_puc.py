# transactions/management/commands/importar_puc.py
from django.core.management.base import BaseCommand
from transactions.models import Account
import pandas as pd

class Command(BaseCommand):
    help = 'Importa el PUC desde un archivo Excel'

    def add_arguments(self, parser):
        parser.add_argument('excel_path', type=str, help='Ruta del archivo Excel con el PUC')

    def handle(self, *args, **options):
        excel_path = options['excel_path']
        
        self.stdout.write(self.style.WARNING(f'📂 Leyendo archivo: {excel_path}'))
        
        try:
            # Leer Excel
            df = pd.read_excel(excel_path)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Archivo leído: {len(df)} filas'))
            
            # Procesar cuentas
            creadas = 0
            actualizadas = 0
            errores = 0
            
            for index, row in df.iterrows():
                try:
                    # Usar nombres exactos de tus columnas
                    code = str(row['Código']).strip()
                    name = str(row['Cuenta Contable']).strip()
                    
                    # Saltar filas vacías o títulos
                    if not code or code == 'nan' or code == 'Código':
                        continue
                    if not name or name == 'nan':
                        continue
                    
                    # Determinar tipo automáticamente por el código
                    tipo = self.determinar_tipo_por_codigo(code)
                    
                    # Crear o actualizar cuenta
                    account, created = Account.objects.update_or_create(
                        code=code,
                        defaults={
                            'name': name,
                            'tipo': tipo
                        }
                    )
                    
                    if created:
                        creadas += 1
                    else:
                        actualizadas += 1
                    
                    if (creadas + actualizadas) % 100 == 0:
                        self.stdout.write(f'⏳ Procesadas: {creadas + actualizadas} cuentas...')
                    
                except Exception as e:
                    errores += 1
                    if errores < 5:  # Mostrar solo los primeros errores
                        self.stdout.write(self.style.ERROR(f'❌ Error en fila {index + 2}: {str(e)}'))
            
            # Resumen
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS(f'✅ Cuentas CREADAS: {creadas}'))
            self.stdout.write(self.style.WARNING(f'🔄 Cuentas ACTUALIZADAS: {actualizadas}'))
            self.stdout.write(self.style.ERROR(f'❌ ERRORES: {errores}'))
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS(f'🎉 Total de cuentas en la base de datos: {Account.objects.count()}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error general: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
    
    def determinar_tipo_por_codigo(self, code):
        """
        Determina el tipo de cuenta según el primer dígito del código PUC colombiano
        
        1 = ACTIVO
        2 = PASIVO
        3 = PATRIMONIO
        4 = INGRESO
        5 = GASTO (Costos y gastos)
        6 = GASTO (Costos de ventas)
        7 = GASTO (Costos de producción)
        """
        if not code:
            return 'GASTO'
        
        primer_digito = code[0]
        
        TIPOS_PUC = {
            '1': 'ACTIVO',
            '2': 'PASIVO',
            '3': 'PATRIMONIO',
            '4': 'INGRESO',
            '5': 'GASTO',
            '6': 'GASTO',
            '7': 'GASTO',
            '8': 'INGRESO',  # Cuentas de orden deudoras
            '9': 'INGRESO',  # Cuentas de orden acreedoras
        }
        
        return TIPOS_PUC.get(primer_digito, 'GASTO')