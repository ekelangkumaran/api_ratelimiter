import json
import re
import redis
from django.http import HttpResponse,JsonResponse
from api_ratelimiter.ratelimiterredis import SlidingWindowCounterRateLimiter
class ApiRateLimiterMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        user=re.sub('user=','',(request.__dict__["META"]["QUERY_STRING"]))
        print("inside rate limiter middleware USER :::: ",user)
        config_from_db = {
            "URL": "/longapi/firstapi/",
            "limitBasedOn": "user",
            "timeWindow": 60,
            "MaxReqLimit": 100,
            "lockPeriod": 10,
            "limitExceeded": "reject",
        }
   
        pipeline = (redis.Redis(host='localhost', port=6379, db=1)).pipeline()
        longapiratelimiter = SlidingWindowCounterRateLimiter(clientid=config_from_db["URL"]+"ek",redispipeline=pipeline,rate = config_from_db["MaxReqLimit"] ,timeWindow=config_from_db["timeWindow"]) 
        if longapiratelimiter.isRequestAllowed(): # Return true if request allowed 
            print('200')
            response = self.get_response(request)
        elif config_from_db["limitExceeded"] == "queue":
            # Producer logic to publish to queue
            return HttpResponse("Ratelimited")
        else: # return false if request not allowed
            print('429')
            header = longapiratelimiter.getHttpResponseHeaders()
            resp = JsonResponse({'success':'false','message':"You have exhausted the api usage limit. Please try again after sometime"}, status=429)
            #resp = HttpResponse("Ratelimited {}".format(json.dumps(header)))
            for key in header.keys():
                resp[key] = header[key]
            return resp
       

        

        # Code to be executed for each request/response after
        # the view is called.

        return response




