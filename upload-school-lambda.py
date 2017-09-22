import boto3
import StringIO
import zipfile
import mimetypes

def lambda_handler(event, context):
    s3 = boto3.resource('s3')
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:eu-west-2:268054990449:Deploy-School-topic')

    location = {
        "bucketName": 'buildschool.rgregson.info',
        "objectKey": 'school.zip'
    }

    try:
        job = event.get("CodePipeline.job")

        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "MyAppBuild":
                    location = artifact["location"]["s3Location"]

        print "Building school from "  + str(location)

        school_bucket = s3.Bucket('school.rgregson.info')
        build_bucket = s3.Bucket(location["bucketName"])

        school_zip = StringIO.StringIO()
        build_bucket.download_fileobj(location["objectKey"], school_zip)

        with zipfile.ZipFile(school_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                school_bucket.upload_fileobj(obj, nm,
                    ExtraArgs={'ContentType': mimetypes.guess_type(nm)[0]})
                school_bucket.Object(nm).Acl().put(ACL='public-read')

        print "Job Done!"
        topic.publish(Subject='Dads School of Rock', Message='Dads School of Rock deployed succesfully')
        if job:
            codepipeline=boto3.client("codepipeline")
            codepipeline.put_job_success_result(jobId=job["id"])
    except:
        topic.publish(Subject='Dads School of Rock Deployment Failure', Message='Dads School NOT deployed succesfully')
        raise


    return 'Hello from Lambda'
