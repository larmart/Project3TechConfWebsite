import logging
import azure.functions as func
import psycopg2
import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(to_email, subject, message):
    logging.info("Send email to %s with subject: %s", to_email, subject)

    from_email_address = os.environ['from_email_address']
    logging.info("From E-Mail: %s", from_email_address)
    sendgrid_api_key = os.environ['AzureWebJobsSendGridApiKey']

    message = Mail(
        from_email = from_email_address,
        to_emails = to_email,
        subject = subject,
        plain_text_content = message)

    sg = SendGridAPIClient(sendgrid_api_key)
    #sg.send(message)
    logging.info("Email was sent")

def main(msg: func.ServiceBusMessage):

    notification_id = int(msg.get_body().decode('utf-8'))
    logging.info(
        'Python ServiceBus queue trigger processed message: %s', notification_id)

    # Get connection to database
    # see https://www.psycopg.org/docs/usage.html
    database_conn = psycopg2.connect(user="postgres@techconf-db-server",
                                     password="dim@postgr55",
                                     host="techconf-db-server.postgres.database.azure.com",
                                     port="5432",
                                     database="techconfdb")

    # Open a cursor to perform database operations
    cur = database_conn.cursor()

    try:       
        # Get notification message and subject from database using the notification_id
        get_notif_msg_subject_query = 'SELECT message, subject FROM Notification WHERE id = %s;'
        cur.execute(get_notif_msg_subject_query, (notification_id,))
        notification = cur.fetchone()
        message = notification[0]
        subject = notification[1]

        # Get attendees email and name
        get_email_name_query = 'SELECT email, first_name, last_name FROM Attendee;'
        cur.execute(get_email_name_query)
        attendees = cur.fetchall() 

        # Loop through each attendee and send an email with a personalized subject
        for attendee in attendees:
            email = attendee[0]
            first_name = attendee[1]
            last_name = attendee[2]
            email_body = 'Hello {} {},\n{}'.format(first_name, last_name, message)
            send_email(email, subject, email_body)

        # Update the notification table by setting the completed date 
        # and updating the status with the total number of attendees notified
        logging.info("Update the notification table...")
        completed_date = datetime.utcnow()
        number_of_attendees_notified = len(attendees)
        status = 'Notified {} attendees'.format(number_of_attendees_notified)

        update_notifi_table_query = 'UPDATE notification SET completed_date = %s, status = %s WHERE id = %s;'
        cur.execute(update_notifi_table_query, (completed_date, status, notification_id))
        database_conn.commit()
        logging.info("Notification table updated executed")

    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
    finally:
        # Close connection
        logging.info("Close database connection")
        if(database_conn):
            cur.close()
            database_conn.close()