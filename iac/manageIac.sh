#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 -a <create|destroy> [-p <password>] [-d <both|mssql|postgresql>] [-r <resource group name>] [-l <location>]"
    exit 1
}

# Default values
deploy="both"
rgname="contosohoteldb"
location="North Europe"

# Parse input parameters
while getopts ":a:p:d:r:l:" opt; do
    case ${opt} in
        a )
            iacAction=$OPTARG
            ;;
        p )
            passwd=$OPTARG
            ;;
        d )
            deploy=$OPTARG
            ;;
        r )
            rgname=$OPTARG
            ;;
        l )
            location=$OPTARG
            ;;
        \? )
            usage
            ;;
    esac
done

# Validate mandatory parameter
if [ -z "$iacAction" ]; then
    usage
fi

if [[ "$iacAction" != "create" && "$iacAction" != "destroy" ]]; then
    echo "Invalid action: $iacAction"
    usage
fi

if [[ "$deploy" != "both" && "$deploy" != "mssql" && "$deploy" != "postgresql" ]]; then
    echo "Invalid deploy option: $deploy"
    usage
fi

# Check for Azure login
if ! az account show &> /dev/null; then
    echo "Please login to Azure using 'az login'"
    exit 1
fi

rgExists=$(az group exists --name $rgname)

# get current script directory
scriptDir=$(dirname "$0")

# Add your logic for create or destroy actions here
if [ "$iacAction" == "create" ]; then
    ThrowOnInvalidPassword "$passwd"
    if [ "$rgExists" == "false" ]; then
        echo "Creating resource group"
        az group create --name "$rgname" --location "$location" --output none
    else
        echo "Resource group already exists"
    fi
    if [ "$deploy" == "both" ] || [ "$deploy" == "mssql" ]; then
        echo "--------------------"
        echo "Deploying MSSQL"
        result=$(az deployment group create --resource-group "$rgname" --template-file "$scriptDir/deploy-sqlserver.bicep" --parameters administratorLoginPassword="$passwd" --query "properties.provisioningState" -o tsv)
        echo "MSSQL deployment result: $result"
        deploymentName="deploy-mssql"
        connectionString=$(az deployment group show --resource-group "$rgname" --name "$deploymentName" --query "properties.outputs.connectionString.value" -o tsv)
        if [ -n "$connectionString" ]; then
            echo -e "\e[32mMSSQL deployment output: MSSQL_CONNECTION_STRING='$connectionString'\e[0m"
        fi
    fi
    if [ "$deploy" == "both" ] || [ "$deploy" == "postgresql" ]; then
        echo "--------------------"
        echo "Deploying PostgreSQL"
        result=$(az deployment group create --resource-group "$rgname" --template-file "$scriptDir/deploy-postgresql.bicep" --parameters administratorLoginPassword="$passwd" --query "properties.provisioningState" -o tsv)
        echo "PostgreSQL deployment result: $result"
        deploymentName="deploy-postgresql"
        connectionString=$(az deployment group show --resource-group "$rgname" --name "$deploymentName" --query "properties.outputs.connectionString.value" -o tsv)
        if [ -n "$connectionString" ]; then
            echo -e "\e[32mPostgreSQL deployment output: POSTGRES_CONNECTION_STRING='$connectionString'\e[0m"
        fi
    fi
elif [ "$iacAction" == "destroy" ]; then
    if [ "$rgExists" == "true" ]; then
        echo "Deleting resource group"
        az group delete --name "$rgname" --yes --no-wait
    else
        echo "Resource group does not exist"
    fi
else
    echo "Invalid action"
    exit 1
fi