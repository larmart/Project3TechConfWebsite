# TechConf Registration Website

## Project Overview
The TechConf website allows attendees to register for an upcoming conference. Administrators can also view the list of attendees and notify all attendees via a personalized email message.

The application is currently working but the following pain points have triggered the need for migration to Azure:
 - The web application is not scalable to handle user load at peak
 - When the admin sends out notifications, it's currently taking a long time because it's looping through all attendees, resulting in some HTTP timeout exceptions
 - The current architecture is not cost-effective 

In this project, you are tasked to do the following:
- Migrate and deploy the pre-existing web app to an Azure App Service
- Migrate a PostgreSQL database backup to an Azure Postgres database instance
- Refactor the notification logic to an Azure Function via a service bus queue message

## Dependencies

You will need to install the following locally:
- [Postgres](https://www.postgresql.org/download/)
- [Visual Studio Code](https://code.visualstudio.com/download)
- [Azure Function tools V3](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=windows%2Ccsharp%2Cbash#install-the-azure-functions-core-tools)
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)
- [Azure Tools for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ms-vscode.vscode-node-azure-pack)

## Project Instructions

### Part 1: Create Azure Resources and Deploy Web App
1. Create a Resource group
2. Create an Azure Postgres Database single server
   - Add a new database `techconfdb`
   - Allow all IPs to connect to database server
   - Restore the database with the backup located in the data folder
3. Create a Service Bus resource with a `notificationqueue` that will be used to communicate between the web and the function
   - Open the web folder and update the following in the `config.py` file
      - `POSTGRES_URL`
      - `POSTGRES_USER`
      - `POSTGRES_PW`
      - `POSTGRES_DB`
      - `SERVICE_BUS_CONNECTION_STRING`
4. Create App Service plan
5. Create a storage account
6. Deploy the web app

### Part 2: Create and Publish Azure Function
1. Create an Azure Function in the `function` folder that is triggered by the service bus queue created in Part 1.

      **Note**: Skeleton code has been provided in the **README** file located in the `function` folder. You will need to copy/paste this code into the `__init.py__` file in the `function` folder.
      - The Azure Function should do the following:
         - Process the message which is the `notification_id`
         - Query the database using `psycopg2` library for the given notification to retrieve the subject and message
         - Query the database to retrieve a list of attendees (**email** and **first name**)
         - Loop through each attendee and send a personalized subject message
         - After the notification, update the notification status with the total number of attendees notified
2. Publish the Azure Function

### Part 3: Refactor `routes.py`
1. Refactor the post logic in `web/app/routes.py -> notification()` using servicebus `queue_client`:
   - The notification method on POST should save the notification object and queue the notification id for the function to pick it up
2. Re-deploy the web app to publish changes

## Monthly Cost Analysis
Complete a month cost analysis of each Azure resource to give an estimate total cost using the table below:

| Azure Resource | Service Tier | Monthly Cost |
| ------------ | ------------ | ------------ |
| *Azure Postgres Database* | Single Server with Basic tier (Gen5 with 1 VCore, 5GB Storage, 7 Days Backup Retention) | 32.82 USD |
| *Azure Service Bus* | Basic tier: 1 million messages per month | 0.05 USD |
| *Azure App Service Plan* | F1: Free 1GB RAM 60min/day compute | 0.00 USD |
| *Application Insights* | 5 GB per billing account per month included | 0.00 USD |
| *Storage Account* | Standard Usage-based data storage pricing, Hot $0,0196 per GB and month | 0.02 USD |
| *Azure Function App* | Consumption | 0,20 USD per million executions |

## Architecture Explanation
In this project a monolithic architecture was refactored to a much more modular cloud architecture - this has the following advantages: 
1. Within the monolithic architecture the web application is not scalable, if the user load is increasing. After the migration to 
   an Azure App Service, the Azure Function App and the Azure Postgres database now auto scaling is available for the different ressources.
2. In the previous architecture the application was not cost-efficient, since resources have to be reserved for the peak load, but these 
   are not used in normal operation with a smaller user load. For example the Azure Functions in this project use the consumption plan.
   Costs are only incurred if the Azure Functions are used. 
   Another example would be to adapt the service tier of the Azure App Service instead of buying new hardware for the on-premises solution.
3. The monolithic architecture was slow in the case, if the admin sends out the notifications. The frontend user has to wait until the e-mails to
   all attendees were sent out - also HTTP timeouts can extend the waiting time. This task is now migrated to a background job using an Azure Funtion App and
   the user has a better experience, when using the frontend.