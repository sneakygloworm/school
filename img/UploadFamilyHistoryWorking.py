import boto3
from botocore.client import Config
import StringIO
import zipfile
#need to specify mimetypes as below.
import mimetypes


def lambda_handler(event, context):
    s3 = boto3.resource('s3')
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:eu-west-2:268054990449:DeployFamilyHistorySite')

    #below added because of codepipeline
    #**************************************************************
    #these locations are used if lambda is invoked manually.
    location = {
        "bucketName": 'build-family-history.rgregson.info',
        "objectKey": 'familyhistory.zip'

    }
    #**************************************************************
    try:
        #Codepipleline needs the next bit
    #**************************************************************
    #these locations are used if the lambda script is invoked by codepipeline.
        job = event.get("CodePipeline.job")

        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "MyAppBuild":
                    location = artifact["location"]["s3Location"]

        print "Building FH1 from "  + str(location)
    #**************************************************************
        #Creating a name for our s3 resource
        s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))

        #define buckets
        familyhistory_bucket = s3.Bucket('family-history.rgregson.info')
        #build_bucket = s3.Bucket('build-family-history.rgregson.info') #old line before lambda mod'
        build_bucket = s3.Bucket(location["bucketName"])

        #creating a StringIO 'in memory' file
        familyhistory_zip = StringIO.StringIO()
        #downloading the file to that object
        #build_bucket.download_fileobj('familyhistory.zip', familyhistory_zip) #old line before lamdba mod'
        build_bucket.download_fileobj(location["objectKey"], familyhistory_zip)

        #using zipfile module to extract, upload and set the ACL
        with zipfile.ZipFile(familyhistory_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                mime_type = mimetypes.guess_type(nm)[0]
                familyhistory_bucket.upload_fileobj(obj, nm,
                    ExtraArgs={'ContentType': str(mime_type)})
                familyhistory_bucket.Object(nm).Acl().put(ACL='public-read')

        print 'Job Done'
        topic.publish(Subject="Family History S3 site", Message="Family History site deployed successfully")

        #**************************************************************
        #This bit is to 'tell' code pipeline that lambda has completed successfully
        if job:
            codepipeline=boto3.client("codepipeline")
            codepipeline.put_job_success_result(jobId=job["id"])
        #**************************************************************

    except:
        topic.publish(Subject="Family History S3 site deployment failure", Message="Family History site was NOT deployed!!")
        raise

    return 'Hello from Lambda'
