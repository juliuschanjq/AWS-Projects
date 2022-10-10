import boto3
from decimal import Decimal
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

print('Loading function')

rekognition = boto3.client('rekognition')
client = boto3.client('sns')


# --------------- Helper Functions to call Rekognition APIs ------------------



def detect_labels(bucket, key):
    response = rekognition.detect_labels(Image={"S3Object": {"Bucket": bucket, "Name": key}})
    

    # Sample code to write response to DynamoDB table 'MyTable' with 'PK' as Primary Key.
    # Note: role used for executing this Lambda function should have write access to the table.
    table = boto3.resource('dynamodb').Table('phototubDB')
    labels = [{'Confidence': Decimal(str(label_prediction['Confidence'])), 'Name': label_prediction['Name']} for label_prediction in response['Labels']]
    
    #To call upon the first label prediction from the array of predicted labels
    firstlabel = response['Labels'][0]
    
    table.put_item(
        Item={
        'Filename': key, 
        'Label': firstlabel['Name'],
        'Confidence': str(firstlabel['Confidence']),
        'Timestamp' : str(datetime.now())
        })
    
    return response
    



# --------------- Main handler ------------------


def lambda_handler(event, context):
    '''Demonstrates S3 trigger that uses
    Rekognition APIs to detect faces, labels and index faces in S3 Object.
    '''
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    try:

        # Calls rekognition DetectLabels API to detect labels in S3 object
        response = detect_labels(bucket, key)
         
        tosend=""
        
        for Label in response["Labels"]:

            
            print ('{0} - {1}%'.format(Label["Name"], Label["Confidence"]))
            tosend+= '{0} - {1}%'.format(Label["Name"], Label["Confidence"])

        
        message = client.publish(TargetArn='arn:aws:sns:ap-southeast-1:758443149415:image-rekognition', Message=tosend, Subject='Uploaded Message Label')
        

        return response
    except Exception as e:
        print(e)
        print("Error processing object {} from bucket {}. ".format(key, bucket) +
              "Make sure your object and bucket exist and your bucket is in the same region as this function.")
        raise e
