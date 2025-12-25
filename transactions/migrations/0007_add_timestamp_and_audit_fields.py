# Generated migration for new fields
# transactions/migrations/0007_add_timestamp_and_audit_fields.py

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('transactions', '0006_company_transaction_prefix_alter_company_name'),
    ]

    operations = [
        # Company - agregar campos de timestamp y nuevos campos
        migrations.AddField(
            model_name='company',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Fecha de creación'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='company',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Última actualización'),
        ),
        migrations.AddField(
            model_name='company',
            name='address',
            field=models.TextField(blank=True, null=True, verbose_name='Dirección'),
        ),
        migrations.AddField(
            model_name='company',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Teléfono'),
        ),
        migrations.AddField(
            model_name='company',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email'),
        ),
        migrations.AddField(
            model_name='company',
            name='is_active',
            field=models.BooleanField(db_index=True, default=True, verbose_name='Activo'),
        ),

        # ThirdParty - agregar campos de timestamp, soft-delete y nuevos campos
        migrations.AddField(
            model_name='thirdparty',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Fecha de creación'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='thirdparty',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Última actualización'),
        ),
        migrations.AddField(
            model_name='thirdparty',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='Eliminado'),
        ),
        migrations.AddField(
            model_name='thirdparty',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha de eliminación'),
        ),
        migrations.AddField(
            model_name='thirdparty',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email'),
        ),
        migrations.AddField(
            model_name='thirdparty',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Teléfono'),
        ),
        migrations.AddField(
            model_name='thirdparty',
            name='address',
            field=models.TextField(blank=True, null=True, verbose_name='Dirección'),
        ),
        migrations.AddField(
            model_name='thirdparty',
            name='contact_name',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Contacto'),
        ),
        migrations.AddField(
            model_name='thirdparty',
            name='notes',
            field=models.TextField(blank=True, null=True, verbose_name='Notas'),
        ),

        # Account - agregar campos de timestamp y nuevos campos
        migrations.AddField(
            model_name='account',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Fecha de creación'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='account',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Última actualización'),
        ),
        migrations.AddField(
            model_name='account',
            name='naturaleza',
            field=models.CharField(blank=True, choices=[('DEBITO', 'Débito'), ('CREDITO', 'Crédito')], max_length=10, null=True, verbose_name='Naturaleza'),
        ),
        migrations.AddField(
            model_name='account',
            name='is_active',
            field=models.BooleanField(db_index=True, default=True, verbose_name='Activo'),
        ),
        migrations.AddField(
            model_name='account',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='Descripción'),
        ),

        # Transaction - agregar campos de timestamp, soft-delete y auditoría
        migrations.AddField(
            model_name='transaction',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Fecha de creación'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transaction',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Última actualización'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='Eliminado'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha de eliminación'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='created_transactions', to=settings.AUTH_USER_MODEL, verbose_name='Creado por'),
        ),

        # Movement - agregar campos de timestamp
        migrations.AddField(
            model_name='movement',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Fecha de creación'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='movement',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Última actualización'),
        ),

        # RecurringTransaction - agregar campos de timestamp
        migrations.AddField(
            model_name='recurringtransaction',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Fecha de creación'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recurringtransaction',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Última actualización'),
        ),
        migrations.AddField(
            model_name='recurringtransaction',
            name='is_active',
            field=models.BooleanField(db_index=True, default=True, verbose_name='Activo'),
        ),
        migrations.AddField(
            model_name='recurringtransaction',
            name='last_generated',
            field=models.DateField(blank=True, null=True, verbose_name='Última generación'),
        ),

        # License - agregar campos de timestamp y nuevos campos
        migrations.AddField(
            model_name='license',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Fecha de creación'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='license',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Última actualización'),
        ),
        migrations.AddField(
            model_name='license',
            name='license_type',
            field=models.CharField(choices=[('TRIAL', 'Prueba'), ('BASIC', 'Básica'), ('PRO', 'Profesional'), ('ENTERPRISE', 'Empresarial')], default='TRIAL', max_length=20, verbose_name='Tipo de licencia'),
        ),
        migrations.AddField(
            model_name='license',
            name='max_companies',
            field=models.IntegerField(default=1, verbose_name='Máximo de empresas'),
        ),

        # AccountingRule - agregar campos de timestamp y nuevos campos
        migrations.AddField(
            model_name='accountingrule',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Fecha de creación'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='accountingrule',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Última actualización'),
        ),
        migrations.AddField(
            model_name='accountingrule',
            name='min_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Monto mínimo'),
        ),
        migrations.AddField(
            model_name='accountingrule',
            name='max_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Monto máximo'),
        ),
        migrations.AddField(
            model_name='accountingrule',
            name='created_by_user',
            field=models.BooleanField(default=False, help_text='True si la creó el usuario, False si la aprendió el sistema', verbose_name='Creado por usuario'),
        ),

        # Crear nuevos modelos
        migrations.CreateModel(
            name='RecurringMovementTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('debit', models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name='Débito')),
                ('credit', models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name='Crédito')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descripción')),
                ('account', models.ForeignKey(on_delete=models.deletion.CASCADE, to='transactions.account', verbose_name='Cuenta')),
                ('recurring_transaction', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='movement_templates', to='transactions.recurringtransaction', verbose_name='Transacción recurrente')),
                ('third_party', models.ForeignKey(on_delete=models.deletion.CASCADE, to='transactions.thirdparty', verbose_name='Tercero')),
            ],
            options={
                'verbose_name': 'Movimiento Plantilla',
                'verbose_name_plural': 'Movimientos Plantilla',
            },
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('CREATE', 'Creación'), ('UPDATE', 'Actualización'), ('DELETE', 'Eliminación'), ('CANCEL', 'Anulación'), ('RESTORE', 'Restauración')], max_length=20, verbose_name='Acción')),
                ('model_name', models.CharField(max_length=100, verbose_name='Modelo')),
                ('object_id', models.IntegerField(verbose_name='ID del objeto')),
                ('object_repr', models.CharField(max_length=255, verbose_name='Representación')),
                ('changes', models.JSONField(blank=True, null=True, verbose_name='Cambios')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP')),
                ('user_agent', models.TextField(blank=True, null=True, verbose_name='User Agent')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Fecha/Hora')),
                ('user', models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Usuario')),
            ],
            options={
                'verbose_name': 'Log de Auditoría',
                'verbose_name_plural': 'Logs de Auditoría',
                'ordering': ['-timestamp'],
            },
        ),
    ]
