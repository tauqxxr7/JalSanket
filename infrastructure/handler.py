"""Read-only Lambda API over exported, validated EvidencePackages in private S3."""
import json
import logging
import os
import re
from datetime import datetime, timezone
from time import perf_counter

logger=logging.getLogger()
logger.setLevel(logging.INFO)


def load_json(key):
    import boto3 # Provided by the AWS Python runtime; never needed for local analytics.
    response=boto3.client('s3').get_object(Bucket=os.environ['DATA_BUCKET'],Key='data/'+key)
    if response['ContentLength'] > 2_000_000:raise ValueError('Artifact exceeds bound')
    with response['Body'] as body:return json.loads(body.read())


def handler(event,context):
    start=perf_counter();status=200;body=None
    request_id=getattr(context,'aws_request_id','unavailable')
    try:
        method=event.get('requestContext',{}).get('http',{}).get('method','')
        path=event.get('rawPath','')
        if method!='GET':status,body=405,{'detail':'Method not allowed'}
        elif event.get('rawQueryString'):status,body=422,{'detail':'This bounded endpoint accepts no query parameters.'}
        elif path=='/api/health':
            network=load_json('network.json')
            body={'status':'ready','mode':network['provenance']['data_mode'],'aws_deployed':True}
        elif path=='/api/network':body=load_json('network.json')
        else:
            match=re.fullmatch(r'/api/stations/(group-[0-9a-f]{16})(/evidence)?',path)
            if not match:status,body=404,{'detail':'Unknown route'}
            else:
                key=match[1]
                network=load_json('network.json')
                if key not in {s['station_group_key'] for s in network['stations']}:
                    status,body=404,{'detail':'Unknown internal station grouping.'}
                else:body=load_json(('evidence/' if match[2] else 'stations/')+key+'.json')
    except Exception:
        status,body=503,{'detail':'Validated S3 snapshot unavailable','request_id':request_id}
    logger.info(json.dumps({'request_id':request_id,'processing_stage':'s3_api','status':status,'latency_ms':round((perf_counter()-start)*1000,2),'timestamp':datetime.now(timezone.utc).isoformat()}))
    return {'statusCode':status,'headers':{'content-type':'application/json','cache-control':'no-store','x-request-id':request_id,'x-content-type-options':'nosniff'},'body':json.dumps(body,allow_nan=False)}
