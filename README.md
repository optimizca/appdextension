# AppDynamics with Office 365
AppDynamics extension checks to see if Office 365 is available


###### Installation

1. Centos
    - Install and Configure the AppDynamics MachineAgent
    - Navigate to the machine agent directory under monitors
    - Clone the github repository
      ```
        git clone https://github.com/optimizca/appdextension.git
      ```
    - Navigate to the Extension's directory
      ```
        cd appdextension
      ```
    - Provide the correct permissions to the executable files
      ```
        chmod 700 appdte.sh 
        chmod 700 appdte.py
      ```
    - Run the bash Script (Centos has a preinstall version of python and therefore there should'nt be any further changes)
      ```
        ./appdte.sh
      ```
    - The First time the code runs creates a script for the AppDynamics analytics schema creation. If needed run this adding the appropriate flags.
      ```
        chmod 700 createSchema.sh
        ./createSchema.sh -h 
        #Example: ./createSchema.sh -sc TE -ac global_account_hehg1h2b3jh5b4324n2nfs -k kkkkk-aaaaa-xxxxx-yyyyy -es "https://fra-ana-api.saas.appdynamics.com" -port 443
      ```
    - Change the frequency under monitor.xml
    - Restart the machine agent
    
##### Configuration Options
 - The extension needs to be configured with proper information in order to function. You will need to follow the following instructions for Office 365:
 1. To allow authentication you first need to register your application at Azure App Registrations.
    1. Login at Azure Portal (App Registrations)
    2. Create an app. Set a name.
    3. In Supported account types choose "Accounts in any organizational directory and personal Microsoft accounts (e.g. Skype, Xbox, Outlook.com)", if you are using a personal       account.
    4. Set the redirect uri (Web) to: https://login.microsoftonline.com/common/oauth2/nativeclient and click register. This needs to be inserted into the "Redirect URI" text box       as simply checking the check box next to this link seems to be insufficent. This is the default redirect uri used by this library, but you can use any other if you want.
    5. Write down the Application (client) ID. You will need this value.

    6. Under "Certificates & secrets", generate a new client secret. Set the expiration preferably to never. Write down the value of the client secret created now. It will be          hidden later on.
    7. Under Api Permissions:
    * add the application permissions for Microsoft Graph you want.
    * Click on the Grant Admin Consent button (if you have admin permissions) or wait until the admin has given consent to your application.
    * As an example, to read and send emails use:
     * Mail.ReadWrite
     * Mail.Send
     * User.Read
       
###### Certificates
  - TLS CA Authority
      The repository comes with a predefined ca-bundle file and configuration defaults to it. The ca-bundle is used to verify AppDynamics endpoints. The user has the ability to point the python script to a preexisting CA bundle or disable the Verification.     
      Default
       ```
        TLSCertificate:
            certificateBundlePath: "certificates/appd-te.ca-bundle"
       ```
      Custom
       ```
        TLSCertificate:
            certificateBundlePath: "<Path_to_CA_Bundle>"
       ```
      Verification Disabled
       ```
        TLSCertificate:
            certificateBundlePath: ""
       ```
