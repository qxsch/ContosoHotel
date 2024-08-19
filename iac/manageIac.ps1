param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet('create', 'destroy')]
    [string]$iacAction,

    [Parameter(Mandatory=$false, Position=1)]
    [string]$passwd = "",

    [Parameter(Mandatory=$false, Position=2)]
    [ValidateSet('both', 'mssql', 'postgresql')]
    [string]$deploy = "both",

    [Parameter(Mandatory=$false, Position=3)]
    [string]$rgname = "contosohoteldb",

    [Parameter(Mandatory=$false, Position=4)]
    [string]$location = "North Europe"
)

# checking for the basics
try {
    $azctx = Get-AzContext -ErrorAction Stop
}
catch {
    throw "Please login to Azure using 'Connect-AzAccount'"
}
if(-not($azctx.Subscription)) {
    throw "Please select a subscription using 'Select-AzSubscription'"
}
Write-Host ( "Deploying to subscription: " + $azctx.Subscription.Id + " (" + $azctx.Subscription.Name + ")" )


function ThrowOnInvalidPassword {
    param (
        [string]$passwd
    )

    if($passwd.Length -lt 8) {
        throw "Password must be at least 8 characters long"
    }
    if(-not($passwd -cmatch "[A-Z]")) {
        throw "Password must contain at least one uppercase letter"
    }
    if(-not($passwd -cmatch "[a-z]")) {
        throw "Password must contain at least one lowercase letter"
    }
    if($passwd -notmatch "[0-9]") {
        throw "Password must contain at least one digit"
    }
    if($passwd -notmatch "[^a-zA-Z0-9]") {
        throw "Password must contain at least one special character"
    }
}

$rgExists = ($null -ne (Get-AzResourceGroup -Name $rgname -ErrorAction SilentlyContinue))

# get current script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

if ($iacAction -eq "create") {
    ThrowOnInvalidPassword -passwd $passwd
    if(-not $rgExists) {
        Write-Host "Creating resource group"
        New-AzResourceGroup -Name $rgname -Location $location -ErrorAction Stop | Out-Null
    }
    else {
        Write-Host "Resource group already exists"
    }
    if($deploy -eq "both" -or $deploy -eq "mssql") {
        Write-Host "--------------------"
        Write-Host "Deploying MSSQL"
        $result = New-AzResourceGroupDeployment -ResourceGroupName $rgname -TemplateFile (Join-Path $scriptDir "deploy-sqlserver.bicep") -administratorLoginPassword $passwd -ErrorAction Stop
        Write-Host "MSSQL deployment result: $($result.ProvisioningState)"
        if($result.Outputs.connectionString) {
            Write-Host -ForegroundColor Green "MSSQL deployment output: MSSQL_CONNECTION_STRING='$($result.Outputs.connectionString.Value)'"
        }
    }
    if($deploy -eq "both" -or $deploy -eq "postgresql") {
        Write-Host "--------------------"
        Write-Host "Deploying PostgreSQL"
        $result = New-AzResourceGroupDeployment -ResourceGroupName $rgname -TemplateFile (Join-Path $scriptDir "deploy-postgresql.bicep") -administratorLoginPassword $passwd -ErrorAction Stop
        Write-Host "PostgreSQL deployment result: $($result.ProvisioningState)"
        if($result.Outputs.connectionString) {
            Write-Host -ForegroundColor Green "PostgreSQL deployment output: POSTGRES_CONNECTION_STRING='$($result.Outputs.connectionString.Value)'"
        }
    }
}
elseif ($iacAction -eq "destroy") {
    if($rgExists) {
        Write-Host "Deleting resource group"
        Remove-AzResourceGroup -Name $rgname -Force -ErrorAction Stop
    }
    else {
        Write-Host "Resource group does not exist"
    }
}
else {
    throw "Invalid action"
}
