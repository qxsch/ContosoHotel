@description('The name of the SQL logical server.')
param serverName string = uniqueString('sql', resourceGroup().id)

@description('The name of the SQL Database.')
param sqlDBName string = 'pycontosohotel'

@description('Location for all resources.')
param location string = resourceGroup().location

@description('The administrator username of the SQL logical server.')
param administratorLogin string = 'contosoadmin'

@description('The administrator password of the SQL logical server.')
param administratorLoginPassword string

resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {
    name: serverName
    location: location
    properties: {
        administratorLogin: administratorLogin
        administratorLoginPassword: administratorLoginPassword
        publicNetworkAccess: 'Enabled'
        restrictOutboundNetworkAccess: 'Disabled'
    }
}

resource sqlFirewallRule 'Microsoft.Sql/servers/firewallRules@2023-08-01-preview' = {
    parent: sqlServer
    name: 'AllowAll'
    properties: {
        startIpAddress: '0.0.0.0'
        endIpAddress: '255.255.255.255'
    }
}

resource sqlDB 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
    parent: sqlServer
    name: sqlDBName
    location: location
    sku: {
        name: 'Basic'
        tier: 'Basic'
        capacity: 5
    }
    properties: {
        collation: 'SQL_Latin1_General_CP1_CI_AS'
        maxSizeBytes: 2147483648
        catalogCollation: 'SQL_Latin1_General_CP1_CI_AS'
        zoneRedundant: false
        readScale: 'Disabled'
        requestedBackupStorageRedundancy: 'local'
        availabilityZone: 'NoPreference'
    }
}




output connectionString string = 'DRIVER={ODBC Driver 18 for SQL Server};SERVER=${sqlServer.properties.fullyQualifiedDomainName};DATABASE=${sqlDB.name};UID=${sqlServer.properties.administratorLogin};PWD=${administratorLoginPassword};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
