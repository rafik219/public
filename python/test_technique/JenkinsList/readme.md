
Description:
------------

This script is used to list all jobs on jenkins servers configured on config.yaml file.
and get information about specific jobs name.

Python version : python3.5


Example:
--------

1/ python JenkinsList.py -h     => Get information how to use script.

2/ python JenkinsList -c config.yaml info   => List all jobs with last status and URL.

3/ python JenkinsList.py -c config.yaml info "test-mono-pull-request-testviewer"    => Get more information for "test-mono-pull-request-testviewer" job.





  # print(response)
                #from random import randrange
#                 response = {u'Ipln_WS_REST_datametrie': {
#                     u'Get_Current_Alarms_Per_Monitor': {
#                         u'status': u'success',
#                           u'response': [{
#                               u'ALARM_TYPE': u'BLACK',
#                               u'MONITOR_ID': 130930,
#                                u'ACK': 0,
#                                 u'RESULT_DATE_GMT': u'17/05/2018 23:15:00',
#                                  u'ALARM_ID': 70118347,
#                                   u'ALARM_START_DATE': u'18/05/2018 01:30:14',
#                                    u'ALARM_START_DATE_GMT': u'17/05/2018 23:30:14',
#                                     u'RESULT_DATE': u'18/05/2018 01:15:00',
#                                     u'ALARM_END_DATE': u'',
#                                     u'ALARM_END_DATE_GMT': u''}
#                                         ]},
#                     u'Api_Version': 3}}
                # response = {u'Ipln_WS_REST_datametrie': {
                #     u'Get_Current_Alarms_Per_Monitor': {
                #         u'status': u'success',
                #           u'response': u''},
                #     u'Api_Version': 3}}