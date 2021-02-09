    #!/bin/bash
    schemaName="office365"
    accountName=""
    apiKey=""
    events_service="https://analytics.api.appdynamics.com"
    port="443"

    while test $# -gt 0; do
        case $1 in
          -h|--help)
             echo "AppDynamics Analytics Schema Creation"
             echo " "
             echo "-------------------------------------"
             echo " "
             echo "options:"
             echo "-h,  --help                show brief help"
             echo "-sc, --schema              AppDynamics Schema Name specify an action to use"
             echo "-ac, --accountname         AppDynamics Global Account Name"
             echo "-k , --key                 AppDynamics Analytics API Key"
             echo "-es                        AppDynamics events service host name, inc protocol Example: https://analytics.api.appdynamics.com"
             echo "-port                      AppDynamics events service port"
             exit 0
         ;;
            -sc | --schema )        shift
                                    schemaName="$1"
                                    ;;
            -ac | --accountname )   shift
                                    accountName="$1"
                                    ;;
            -k | --key )            shift
                                    apiKey="$1"
                                    ;;
            -es)                    shift
                                    events_service="$1"
                                    ;;
            -port)                  shift
                                    port=$1
                                    ;;
            * )                     usage
                                    exit 1
         esac
         shift
     done
    curl -X POST "${events_service}:${port}/events/schema/$schemaName" -H"X-Events-API-AccountName:${accountName}" -H"X-Events-API-Key:${apiKey}" -H"Content-type: application/vnd.appd.events+json;v=2" -d '{"schema":{"tenantId": "string", "serverName": "string", "status": "string", "location": "string", "destination": "string", "senderEmail": "string", "time_to_auth": "float", "time_to_send": "float"}}'