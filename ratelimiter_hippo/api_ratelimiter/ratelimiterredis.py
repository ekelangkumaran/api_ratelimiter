import datetime
import time


class SlidingWindowCounterRateLimiter:

    '''Sliding Window Counter Rate Limiter.'''

    def __init__(self, clientid, redispipeline, rate=10, time_window_unit='second',timeWindow=60, max_no_time_window_for_deletion=5):
        '''Initilize all properties of rate limiter.'''

        # redis pipeline
        self.pipeline = redispipeline


        # client id
        self.clientid = clientid

        # rate limit
        self.rate = rate

        # Time Window  ('per')
        self.time_window = timeWindow

        # Unit of Time Window
        self.time_window_unit = time_window_unit

        # Total requert served
        self.total_request_served = 0


        self.request_recieved_timestamp_in_TW_format = None
        self.request_recieved_at = None



        # Reduce memeory footprint when old/expired fixed time window reached at some number.
        self.max_no_time_window_for_deletion = max_no_time_window_for_deletion

        # Set dynamically rate limit time window
        self.windowTimeKwargs = {self.time_window_unit + 's': self.time_window}

        # Set time window time format
        self.expiration_time_of_client_keys = self.time_window + self.time_window
        self.fixed_time_window_format_for_insertion = "%Y:%m:%d:%H:%M:%S"
        self.fixed_time_window_format_for_ratelimit_reset = "%Y-%m-%d-%H-%M-%S"
       
    def __setRequest_Recieved_Timestamp(self):
        '''Set request recieved time in different formats.
            Set request recieved at datetime format.
            Set request recieved timestamp for rate limit reset time in rate limit unit format.
            Set request recieved timestamp for increement the Fixed Time Window counter in ftW insertion format.
        '''

        self.request_recieved_at = datetime.datetime.now()

        self.request_recieved_timestamp_for_ratelimit_reset = self.request_recieved_at.strftime(
            self.fixed_time_window_format_for_ratelimit_reset)

        # Get current time based on window time interval format.
        currentTime = self.request_recieved_at.strftime(
            self.fixed_time_window_format_for_insertion)
        self.request_recieved_timestamp_in_TW_format = int(datetime.datetime.timestamp(datetime.datetime.strptime(
            currentTime, self.fixed_time_window_format_for_insertion)))  # Converting into unix timestamp

    def __setSlidingTimeWindowTimestamp(self):
        '''Set sliding time window time in timestamp.
        Subtracting rate limit time window from  request recived time, foramt in FTW_format_for_insertion format and then into timestamp.
        '''
        #60 secs(timewindow) before the request arrived
        self.slidingTimeWindow = self.request_recieved_at - \
            datetime.timedelta(**self.windowTimeKwargs)

        self.slidingTimeWindow = datetime.datetime.strftime(
            self.slidingTimeWindow, self.fixed_time_window_format_for_insertion)
        self.slidingTimeWindow = datetime.datetime.strptime(
            self.slidingTimeWindow, self.fixed_time_window_format_for_insertion)
        self.slidingTimeWindow = int(
            datetime.datetime.timestamp(self.slidingTimeWindow))

    def isRequestAllowed(self):
        '''Returns True if request allowed otherwise False.'''

        # Set current  timestamp in time window   format for increement counter
        self.__setRequest_Recieved_Timestamp()
        
        # Increement counter into current  time window
        self.pipeline.execute_command(
            'HINCRBY', self.clientid, self.request_recieved_timestamp_in_TW_format, 1)

        # Get all windows
        self.pipeline.execute_command('HGETALL', self.clientid)

        # Set expiration time
        self.pipeline.execute_command(
            'EXPIRE', self.clientid, self.expiration_time_of_client_keys)

        # Execute Redus pipeline
        result = self.pipeline.execute()

        # Get all time windows from result list
        time_window_list = result[1]

        # Set sliding time window
        self.__setSlidingTimeWindowTimestamp()

        # Trim and count requests served in rate limit time window
        self.__trim_old_and_count_requests_in_time_window(time_window_list)

        # Delete expired FTW
        if self.__is_expired_time_windows_exists and (self.max_no_time_window_for_deletion > self.total_expired_time_windows ):
            self.pipeline.execute()

        # If request in window greater then rate then return False otherwise True
        if self.total_request_served > self.rate:

            self.is_request_allowed = False
            return False
        else:
            self.is_request_allowed = True
            return True

    def __get_FTW_created_at_deltatime(self):
        '''Returns FTW created at time with addition of rate limit time window for rate limit reset header.
        Instead of adding rate limit time window on each request i stored when FTW created first time.'''

        resetTime = self.request_recieved_at + \
            datetime.timedelta(**self.windowTimeKwargs)
        return datetime.datetime.timestamp(resetTime)

    def __set_ratelimit_reset_time(self, current_fixed_time_window_created_at):
        '''Set ratelimit reset time. 
        Fixed Time Window first time created time passed as a parameter. Subtracing the request recived time from FTW time. 
        '''

        self.x_ratelimit_reset = None
        current_fixed_time_window_created_at = current_fixed_time_window_created_at.decode()
        self.x_ratelimit_reset = datetime.datetime.fromtimestamp(
            float(current_fixed_time_window_created_at)) - self.request_recieved_at

    def get_x_ratelimit_reset(self, in_seconds=True):
        '''Returns x-ratelimit-reset in seconds or in str format.'''

        if in_seconds:
            return self.x_ratelimit_reset.total_seconds()
        else:
            return self.x_ratelimit_reset

    def __trim_old_and_count_requests_in_time_window(self, time_window_list):
        '''Counts no of reqeuest served in rate limit time window, insert time windows into pipeline which are less then
        sliding time window, set True if any expired  fixed time window exists and count total expired windows.
        '''

        self.__is_expired_time_windows_exists = False
        self.total_expired_time_windows = 0

        for window, counts in time_window_list.items():

            if int(window.decode()) < self.slidingTimeWindow:  # Check each window expired or not

                # Insert all expired windows into pipeline
                self.pipeline.execute_command(
                    'HDEL', self.clientid, int(window.decode()))

                # Set if some windows expired for delete expired windows
                self.__is_expired_time_windows_exists = True

                # Count no of expired windows
                self.total_expired_time_windows = self.total_expired_time_windows + 1

            else:  # if windows not expired then count all requests

                # Counts request in window size
                self.total_request_served = self.total_request_served + \
                    int(counts.decode())

    def get_retry_after(self):
        ''' Returns retry after header.'''

        retry_after = self.request_recieved_at + \
            datetime.timedelta(**self.windowTimeKwargs)
        return retry_after.strftime("%Y:%m:%d:%H:%M:%S:%M")

    def get_x_ratelimit_remaining(self):
        '''Returns rate limit remaining requests.
        Subtracting total request served from max allowed requests. 
        '''

        remaining_request = self.getMaxRequestsAllowed() - self.total_request_served

        if remaining_request <= 0:
            return 0
        else:
            return remaining_request

    def getMaxRequestsAllowed(self):
        '''Returns max no of requests allowed.'''

        return self.rate

    def getTotalRequestServedInSlidingWindow(self):
        '''Returns total request served in rate limit time window'''

        return self.total_request_served

    def getHttpResponseHeaders(self):
        '''Returns Http reseponse headers.
            X-RateLimit-Limit.
            X_RateLimit_Remaining.
            X-RateLimit-Reset.
        '''

        HttpResponseHeaders = {

            'X-RateLimit-Limit': self.getMaxRequestsAllowed(),  # Max requests allowed
            'X_RateLimit_Remaining': self.get_x_ratelimit_remaining(),  # Remaing allowed requests

        }


        # If status code 429 then Retry after header
        if not self.is_request_allowed:
            HttpResponseHeaders['Retry-after'] = self.get_retry_after()

        return HttpResponseHeaders