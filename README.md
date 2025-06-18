# Bank Statements Processor

Este proyecto procesa extractos bancarios de diferentes bancos (BCP, BNB, UNION) y los estandariza para su importación a una base de datos SQL.

## Estructura del Proyecto

```
bank-statements/
├── data/
│   ├── raw/           # Archivos Excel originales de los bancos
│   └── processed/     # Archivos CSV procesados y estandarizados
├── src/
│   ├── cleaner/      # Módulos de limpieza por banco
│   ├── detector/     # Detector automático de banco
│   ├── enricher/     # Enriquecedor de datos (ej: BCP con detalles de pagos)
│   ├── processors/   # Procesadores específicos por banco
│   ├── reader/       # Lector de archivos Excel
│   ├── utils/        # Utilidades comunes
│   └── workflows/    # Flujos de trabajo por banco
└── tests/           # Pruebas unitarias
```

## Formato de Salida Estandarizado

Los archivos procesados siguen un formato estandarizado que coincide con la estructura de la tabla `bank_statements`:

### Columnas Estandarizadas

| Columna            | Tipo          | Descripción                             | Ejemplo              |
|-------------------|---------------|----------------------------------------|---------------------|
| bank_code         | VARCHAR(10)   | Código del banco (BCP/BNB/UNION)       | "BCP"               |
| account_number    | VARCHAR(50)   | Número de cuenta                       | "201204"            |
| company_voucher   | VARCHAR(100)  | Voucher único generado                 | "BCP-20250502-122339"|
| bank_voucher      | VARCHAR(100)  | Voucher original del banco             | "122339"            |
| transaction_date  | DATE          | Fecha de transacción                   | "2025-05-02"        |
| transaction_time  | TIME          | Hora de transacción                    | "10:14:28"          |
| description       | TEXT          | Descripción de la operación            | "PAGO FACTURA 123"  |
| transaction_type  | VARCHAR(20)   | Tipo de transacción                    | "2401"              |
| reference_number  | VARCHAR(100)  | Número de referencia                   | "122339"            |
| transaction_code  | VARCHAR(50)   | Código interno del banco               | "2401"              |
| debit_amount      | DECIMAL(15,2) | Monto de débito (positivo)            | 4500.00             |
| credit_amount     | DECIMAL(15,2) | Monto de crédito (positivo)           | 29262.00            |
| balance           | DECIMAL(15,2) | Saldo después de la transacción        | 1097914.04          |
| itf_amount        | DECIMAL(8,2)  | Impuesto a las Transacciones          | 0.00                |
| branch_office     | VARCHAR(100)  | Oficina o sucursal                     | "La Paz"            |
| agency_code       | VARCHAR(20)   | Código de agencia                      | "201204"            |
| user_code         | VARCHAR(50)   | Usuario que procesó                    | "TLC"               |
| operation_number  | VARCHAR(50)   | Número de operación                    | "122339"            |
| additional_details| TEXT          | Detalles adicionales                   | "TITULAR - GLOSA"   |
| import_batch_id   | VARCHAR(36)   | UUID del lote de importación          | "uuid-v4..."        |

## Mapeo por Banco

### BCP
- Fecha → transaction_date (convertido a YYYY-MM-DD)
- Hora → transaction_time
- Glosa → description
- Tipo → transaction_type y transaction_code
- Suc. Age. → agency_code y account_number
- Usuario → user_code
- Importe → debit_amount o credit_amount (según signo)
- Nro. Operación → bank_voucher, reference_number, operation_number
- Adicionales → additional_details

### UNION
- Fecha Movimiento → transaction_date
- AG → branch_office y agency_code
- Descripción → description
- Nro Documento → bank_voucher, reference_number
- Monto → debit_amount o credit_amount (según signo)
- Adicionales → additional_details

## Uso

Para procesar un archivo:

```bash
python -m src.main <archivo.xls>
```

Ejemplo:
```bash
python -m src.main bcpHistoricos.xls
```

## Características Especiales

1. **Generación de Voucher Único**:
   - Formato: {BANCO}-{YYYYMMDD}-{VOUCHER}
   - Ejemplo: "BCP-20250502-122339"

2. **Manejo de Montos**:
   - Débitos: Valores positivos en debit_amount (montos negativos en el extracto)
   - Créditos: Valores positivos en credit_amount (montos positivos en el extracto)
   - Balance: Saldo después de cada transacción

3. **Enriquecimiento de Datos**:
   - BCP: Integración con reporte de pagos para detalles adicionales
   - Campo adicionales: Información extra del pagador/beneficiario

4. **Control de Calidad**:
   - Validación de formatos de fecha y montos
   - Limpieza de espacios y caracteres especiales
   - UUID único por lote de importación
   - Control de duplicados por company_voucher

## Base de Datos Destino

Los datos procesados están diseñados para ser importados en la tabla `bank_statements` con la siguiente estructura:

```sql
CREATE TABLE `bank_statements` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `bank_code` varchar(10) NOT NULL COMMENT 'BNB1, BNB2, BNBUSD, BCP, UNION',
  `account_number` varchar(50) NOT NULL COMMENT 'Número de cuenta',
  `company_voucher` varchar(100) NOT NULL COMMENT 'Voucher único generado por la empresa',
  `bank_voucher` varchar(100) DEFAULT NULL COMMENT 'Voucher/código original del banco',
  `transaction_date` date NOT NULL COMMENT 'Fecha de la transacción',
  `transaction_time` time DEFAULT NULL COMMENT 'Hora de la transacción',
  `processing_datetime` datetime GENERATED ALWAYS AS (
    CASE 
      WHEN transaction_time IS NOT NULL THEN TIMESTAMP(transaction_date,transaction_time) 
      ELSE TIMESTAMP(transaction_date,'00:00:00') 
    END
  ) STORED COMMENT 'Fecha y hora combinadas',
  `description` text NOT NULL COMMENT 'Descripción de la operación',
  `transaction_type` varchar(20) DEFAULT NULL COMMENT 'Tipo de transacción (DEBIT/CREDIT/TRANSFER/etc)',
  `reference_number` varchar(100) DEFAULT NULL COMMENT 'Número de referencia o documento',
  `transaction_code` varchar(50) DEFAULT NULL COMMENT 'Código interno de transacción del banco',
  `debit_amount` decimal(15,2) DEFAULT NULL COMMENT 'Monto de débito',
  `credit_amount` decimal(15,2) DEFAULT NULL COMMENT 'Monto de crédito',
  `net_amount` decimal(15,2) GENERATED ALWAYS AS (
    COALESCE(credit_amount,0) - COALESCE(debit_amount,0)
  ) STORED COMMENT 'Monto neto',
  `balance` decimal(15,2) NOT NULL COMMENT 'Saldo después de la transacción',
  `itf_amount` decimal(8,2) DEFAULT '0.00' COMMENT 'Impuesto a las Transacciones Financieras',
  `branch_office` varchar(100) DEFAULT NULL COMMENT 'Oficina o sucursal',
  `agency_code` varchar(20) DEFAULT NULL COMMENT 'Código de agencia',
  `user_code` varchar(50) DEFAULT NULL COMMENT 'Usuario que procesó (para BCP)',
  `operation_number` varchar(50) DEFAULT NULL COMMENT 'Número de operación',
  `additional_details` text COMMENT 'Detalles adicionales o observaciones',
  `import_batch_id` varchar(36) DEFAULT NULL COMMENT 'ID del lote de importación',
  PRIMARY KEY (`id`),
  UNIQUE KEY `company_voucher` (`company_voucher`),
  KEY `idx_bank_account` (`bank_code`,`account_number`),
  KEY `idx_date` (`transaction_date`),
  KEY `idx_datetime` (`processing_datetime`),
  CONSTRAINT `chk_amounts` CHECK (
    (debit_amount IS NOT NULL AND debit_amount >= 0) OR 
    (credit_amount IS NOT NULL AND credit_amount >= 0)
  ),
  CONSTRAINT `chk_bank_code` CHECK (
    bank_code IN ('BNB1','BNB2','BNBUSD','BCP','UNION')
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Restricciones Importantes

1. **Validación de Montos**:
   - Los montos de débito y crédito deben ser positivos o NULL
   - Al menos uno de los dos (débito o crédito) debe tener valor
   - El monto neto se calcula automáticamente

2. **Códigos de Banco**:
   - Valores permitidos: 'BNB1', 'BNB2', 'BNBUSD', 'BCP', 'UNION'
   - No se permiten otros códigos de banco

3. **Unicidad**:
   - El campo `company_voucher` debe ser único
   - Se usa como identificador único de la transacción

4. **Campos Calculados**:
   - `processing_datetime`: Combina fecha y hora automáticamente
   - `net_amount`: Calcula el monto neto (crédito - débito)

### Índices Disponibles

1. **Claves Primarias y Únicas**:
   - `id`: Clave primaria autoincremental
   - `company_voucher`: Índice único

2. **Índices de Búsqueda**:
   - `idx_bank_account`: Búsquedas por banco y cuenta
   - `idx_date`: Búsquedas por fecha
   - `idx_datetime`: Búsquedas por fecha y hora
   - `idx_reference`: Búsquedas por número de referencia
   - `idx_batch`: Búsquedas por lote de importación

## Notas Importantes

1. **Formato de Datos**:
   - Los montos siempre se almacenan como positivos en sus respectivas columnas
   - Las fechas se estandarizan a formato ISO (YYYY-MM-DD)
   - Las horas en formato 24 horas (HH:MM:SS)
   - Todos los montos en formato decimal sin separadores de miles

2. **Campos Calculados**:
   - company_voucher: Generado automáticamente para cada transacción
   - import_batch_id: UUID v4 único por lote de procesamiento
   - processing_datetime: Calculado por la base de datos combinando fecha y hora

3. **Manejo de Valores Nulos**:
   - transaction_time: NULL si no está disponible
   - branch_office: NULL si no está especificado
   - itf_amount: 0.00 por defecto
   - additional_details: NULL si no hay información adicional

4. **Consideraciones Específicas por Banco**:
   - BCP: Incluye códigos de transacción específicos (2401, 3001, etc.)
   - UNION: Utiliza códigos de agencia como parte del branch_office
   - BNB: (Documentación pendiente)
