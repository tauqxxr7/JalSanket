"""Generate reviewable CloudFormation and validated static data; never provision."""
import json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.api import create_app
from backend.provider import ROOT

ref=lambda name:{'Ref':name}
sub=lambda value:{'Fn::Sub':value}
att=lambda name,value:{'Fn::GetAtt':[name,value]}


def template():
    resources={}
    def add(name,kind,properties,**extra):resources[name]={'Type':'AWS::'+kind,'Properties':properties,**extra}
    add('DataBucket','S3::Bucket',{'PublicAccessBlockConfiguration':dict(BlockPublicAcls=True,IgnorePublicAcls=True,BlockPublicPolicy=True,RestrictPublicBuckets=True),'BucketEncryption':{'ServerSideEncryptionConfiguration':[{'ServerSideEncryptionByDefault':{'SSEAlgorithm':'AES256'}}]},'OwnershipControls':{'Rules':[{'ObjectOwnership':'BucketOwnerEnforced'}]}},DeletionPolicy='Retain',UpdateReplacePolicy='Retain')
    add('ApiLogs','Logs::LogGroup',{'LogGroupName':sub('/aws/lambda/${AWS::StackName}-api'),'RetentionInDays':7})
    add('ApiRole','IAM::Role',{'AssumeRolePolicyDocument':{'Version':'2012-10-17','Statement':[{'Effect':'Allow','Principal':{'Service':'lambda.amazonaws.com'},'Action':'sts:AssumeRole'}]},'Policies':[{'PolicyName':'ReadEvidenceAndWriteOwnLogs','PolicyDocument':{'Version':'2012-10-17','Statement':[{'Effect':'Allow','Action':['s3:GetObject'],'Resource':sub('${DataBucket.Arn}/data/*')},{'Effect':'Allow','Action':['logs:CreateLogStream','logs:PutLogEvents'],'Resource':att('ApiLogs','Arn')}]}}]})
    add('ApiFunction','Lambda::Function',{'FunctionName':sub('${AWS::StackName}-api'),'Runtime':'python3.12','Handler':'index.handler','Role':att('ApiRole','Arn'),'MemorySize':128,'Timeout':10,'ReservedConcurrentExecutions':2,'Environment':{'Variables':{'DATA_BUCKET':ref('DataBucket')}},'Code':{'ZipFile':(ROOT/'infrastructure/handler.py').read_text(encoding='utf-8')}})
    add('HttpApi','ApiGatewayV2::Api',{'Name':sub('${AWS::StackName}-api'),'ProtocolType':'HTTP'})
    add('Integration','ApiGatewayV2::Integration',{'ApiId':ref('HttpApi'),'IntegrationType':'AWS_PROXY','IntegrationUri':att('ApiFunction','Arn'),'PayloadFormatVersion':'2.0','TimeoutInMillis':10000})
    add('Route','ApiGatewayV2::Route',{'ApiId':ref('HttpApi'),'RouteKey':'$default','Target':{'Fn::Join':['/',['integrations',ref('Integration')]]}})
    add('Stage','ApiGatewayV2::Stage',{'ApiId':ref('HttpApi'),'StageName':'$default','AutoDeploy':True,'DefaultRouteSettings':{'ThrottlingBurstLimit':10,'ThrottlingRateLimit':5}})
    add('InvokePermission','Lambda::Permission',{'Action':'lambda:InvokeFunction','FunctionName':ref('ApiFunction'),'Principal':'apigateway.amazonaws.com','SourceArn':sub('arn:${AWS::Partition}:execute-api:${AWS::Region}:${AWS::AccountId}:${HttpApi}/*')})
    add('OriginAccess','CloudFront::OriginAccessControl',{'OriginAccessControlConfig':{'Name':sub('${AWS::StackName}-s3'),'OriginAccessControlOriginType':'s3','SigningBehavior':'always','SigningProtocol':'sigv4'}})
    add('NoCache','CloudFront::CachePolicy',{'CachePolicyConfig':{'Name':sub('${AWS::StackName}-no-cache'),'DefaultTTL':0,'MaxTTL':0,'MinTTL':0,'ParametersInCacheKeyAndForwardedToOrigin':{'EnableAcceptEncodingGzip':False,'CookiesConfig':{'CookieBehavior':'none'},'HeadersConfig':{'HeaderBehavior':'none'},'QueryStringsConfig':{'QueryStringBehavior':'none'}}}})
    add('ApiQueries','CloudFront::OriginRequestPolicy',{'OriginRequestPolicyConfig':{'Name':sub('${AWS::StackName}-api-query'),'CookiesConfig':{'CookieBehavior':'none'},'HeadersConfig':{'HeaderBehavior':'none'},'QueryStringsConfig':{'QueryStringBehavior':'all'}}})
    add('SecurityHeaders','CloudFront::ResponseHeadersPolicy',{'ResponseHeadersPolicyConfig':{'Name':sub('${AWS::StackName}-headers'),'SecurityHeadersConfig':{'ContentSecurityPolicy':{'ContentSecurityPolicy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'",'Override':True},'ContentTypeOptions':{'Override':True},'ReferrerPolicy':{'ReferrerPolicy':'no-referrer','Override':True}}}})
    behavior={'ViewerProtocolPolicy':'redirect-to-https','AllowedMethods':['GET','HEAD','OPTIONS'],'CachedMethods':['GET','HEAD'],'CachePolicyId':ref('NoCache'),'ResponseHeadersPolicyId':ref('SecurityHeaders')}
    add('Distribution','CloudFront::Distribution',{'DistributionConfig':{'Enabled':True,'DefaultRootObject':'index.html','PriceClass':'PriceClass_200','Origins':[{'Id':'assets','DomainName':att('DataBucket','RegionalDomainName'),'OriginPath':'/frontend','OriginAccessControlId':ref('OriginAccess'),'S3OriginConfig':{'OriginAccessIdentity':''}},{'Id':'api','DomainName':sub('${HttpApi}.execute-api.${AWS::Region}.amazonaws.com'),'CustomOriginConfig':{'OriginProtocolPolicy':'https-only','OriginSSLProtocols':['TLSv1.2']}}],'DefaultCacheBehavior':behavior|{'TargetOriginId':'assets'},'CacheBehaviors':[behavior|{'PathPattern':'/api/*','TargetOriginId':'api','OriginRequestPolicyId':ref('ApiQueries')}],'ViewerCertificate':{'CloudFrontDefaultCertificate':True}}})
    add('BucketPolicy','S3::BucketPolicy',{'Bucket':ref('DataBucket'),'PolicyDocument':{'Version':'2012-10-17','Statement':[{'Effect':'Allow','Principal':{'Service':'cloudfront.amazonaws.com'},'Action':'s3:GetObject','Resource':sub('${DataBucket.Arn}/frontend/*'),'Condition':{'StringEquals':{'AWS:SourceArn':sub('arn:${AWS::Partition}:cloudfront::${AWS::AccountId}:distribution/${Distribution}')}}},{'Effect':'Deny','Principal':'*','Action':'s3:*','Resource':[att('DataBucket','Arn'),sub('${DataBucket.Arn}/*')],'Condition':{'Bool':{'aws:SecureTransport':'false'}}}]}})
    return {'AWSTemplateFormatVersion':'2010-09-09','Description':'JalSanket bounded cached-official read-only demo. Billable; approval required.','Resources':resources,'Outputs':{'Bucket':{'Value':ref('DataBucket')},'FrontendUrl':{'Value':sub('https://${Distribution.DomainName}')},'ApiUrl':{'Value':att('HttpApi','ApiEndpoint')},'LogGroup':{'Value':ref('ApiLogs')}}}


def build():
    output=ROOT/'dist-cloud';output.mkdir(exist_ok=True)
    (output/'template.json').write_text(json.dumps(template(),indent=2)+'\n',encoding='utf-8')
    with TestClient(create_app()) as client:
        network=client.get('/api/network');network.raise_for_status()
        data=network.json();directory=output/'data';directory.mkdir(exist_ok=True)
        (directory/'network.json').write_text(json.dumps(data),encoding='utf-8')
        for station in data['stations']:
            key=station['station_group_key']
            for folder,suffix in [('stations',''),('evidence','/evidence')]:
                target=directory/folder;target.mkdir(exist_ok=True)
                response=client.get('/api/stations/'+key+suffix);response.raise_for_status()
                (target/(key+'.json')).write_text(json.dumps(response.json()),encoding='utf-8')
    print('Prepared CloudFormation and 11 validated API artifacts; no AWS calls made.')


if __name__=='__main__':build()
