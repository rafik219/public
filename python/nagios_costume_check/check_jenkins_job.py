#!/usr/bin/python
# -*- coding: utf-8

#
# author: rbo
# version: 04/04/2017
#
# script: supervision des jobs jenkins via Nagios
# utilisation de api REST Jenkins
#
# 12/04/2017: rbo add --file option
# 01/07/2017: rbo add http authentication
#

import getopt
import json
import os
import sys
import urllib
import urllib2
import base64
from datetime import datetime


def usage():
    print "--------------------------------------------------------"
    print "Usage:"
    print "\t %s -l <jobs>" % sys.argv[0]
    print "\t %s --list <jobs>" % sys.argv[0]
    print " OU:"
    print "\t %s -e <jobn>" % sys.argv[0]
    print "\t %s --exist <jobn>" % sys.argv[0]
    print " OU:"
    print "\t %s -c <jobn>" % sys.argv[0]
    print "\t %s --check <jobn>" % sys.argv[0]
    print " OU:"
    print "\t %s -f <file>" % sys.argv[0]
    print "\t %s --file <file>" % sys.argv[0]
    print "\n<jobs> = jobs : List all jenkins jobs"
    print "\n<jobn> = jobn : Job name, exp: 'Dataviz Report'"
    print "\n<file> = file : File listing the jobs to be monitored"
    print "--------------------------------------------------------"
    sys.exit(-3)


class JenkinsApi:

    def __init__(self):
        # api for python JSON not valid
        self.jenkins_url = "http://0.0.0.0:8080"
        self.jenkins_api_url = self.jenkins_url + "/api/json?pretty=true"
        self.username = "jenkins_user@ip-label.com"
        self.api_token = "01xxx974406xxxx63da7dxxxxxfxxx91"
        self.url_instance = None
        self.json_resp = None
        self.ok_status = 0
        self.warning_status = 1
        self.critical_status = 2
        self.unknown_status = 3
        self.disabled_job = list()
        self.enabled_job = list()
        self.notbuilt_job = list()
        self.get_json_resp()
        self.get_lists_jobs()
        self.version = "0.1"

    def get_json_resp(self, url=None):
        if url is None:
            url = self.jenkins_api_url
        request = urllib2.Request(url)
        base64string = base64.encodestring("%s:%s" % (self.username, self.api_token)).replace("\n", "")
        request.add_header("Authorization", "Basic %s" % base64string)
        try:
            self.url_instance = urllib2.urlopen(request)
        except urllib2.HTTPError, ex:
            print "Error during Authentication, cause: %s" % ex.code
            sys.exit(-1)
        try:
            self.json_resp = json.load(self.url_instance)
        except Exception as e:
            print "Failed to load Json file response :" + e.message
            # return None
            sys.exit(-2)
        return self.json_resp

    def get_lists_jobs(self):
        for job in self.json_resp['jobs']:
            if job['color'] == 'disabled':
                self.disabled_job.append(job)
            elif job['color'] == 'blue':
                self.enabled_job.append(job)
            elif job['color'] == 'red':
                self.enabled_job.append(job)
            elif job['color'] == 'notbuilt':
                self.notbuilt_job.append(job)
            else:
                self.notbuilt_job.append(job)
        return self.enabled_job, self.disabled_job, self.notbuilt_job

    def display_details_jobs(self):
        # enabled_job, disabled_job = self.get_lists_jobs()
        print "Listing enabled jobs:"
        print "\tCount: %s" % len(self.enabled_job)
        for job in self.enabled_job:
            print "\t\t +Status: %s, Name: %s" % (
                "SUCCESS" if job['color'] == "blue" else "FAILURE" if job['color'] == "red" else job['color'].upper(),
                job['name'])
        print "\n"
        print "Listing disabled jobs:"
        print "\tCount: %s" % len(self.disabled_job)
        for job in self.disabled_job:
            # print "\t\t - %s" % job['name']
            print "\t\t +Status: %s, Name: %s" % (job['color'].upper(), job['name'])
        print "Total Count jobs: %s" % str(len(self.enabled_job) + len(self.disabled_job))

    def exist_jobs(self, job_name):
        # enabled_job, disabled_job = self.get_lists_jobs()
        (found, status) = (False, None)
        if job_name in [job_names['name'].lower() for job_names in self.enabled_job]:
            (found, status) = (True, "Enabled")
        elif job_name in [job_names['name'].lower() for job_names in self.disabled_job]:
            (found, status) = (True, "Disabled")
        elif job_name in [job_names['name'].lower() for job_names in self.notbuilt_job]:
            (found, status) = (True, "Notbuilt")
        return found, status

    def get_version(self):
        return self.version


# Main program
if __name__ == "__main__":

    argument = sys.argv[1:]

    if len(argument) < 2:
        usage()

    opts = None
    args = None
    try:
        opts, args = getopt.getopt(argument, "l:c:e:f:v:h", ["list=", "check=", "exist=", "file=", "version=", "help="])
    except getopt.GetoptError, ex:
        print str(ex)
        usage()

    for opt, arg in opts:
        if opt in ("-h", '--help'):
            usage()
        elif opt in ("-l", "--list"):
            param = arg.strip().lower()
            if param != "jobs":
                usage()
            else:
                JenkinsApi().display_details_jobs()
        elif opt in ("-v", "--version"):
            print JenkinsApi().get_version()
        elif opt in ("-e", "--exist"):
            job_name = arg.strip().lower()
            exist, status = JenkinsApi().exist_jobs(job_name)
            if exist:
                print "\t=> Job found: '%s' \n\t=> Status: %s" % (job_name, status)
            else:
                print "\t=> Job Not found: '%s' \n\t=> Status: %s" % (job_name, status)
        elif opt in ("-c", "--check"):
            job_name = arg.strip()
            jenkins = JenkinsApi()
            exist, status = jenkins.exist_jobs(job_name.lower())
            if exist:
                if status == "Enabled":
                    job_url_rest = jenkins.jenkins_url + "/job/" + urllib.quote(job_name) + "/lastBuild/api/json"
                    resp = jenkins.get_json_resp(url=job_url_rest)
                    timestamp = resp.get('timestamp')
                    # utc time
                    date_exec = datetime.utcfromtimestamp(float(timestamp) / 1000.).strftime("%Y-%m-%d %H:%M:%S")
                    if resp.get('result').upper() == "SUCCESS":
                        print "OK: last build end with success at %s" % date_exec
                        sys.exit(jenkins.ok_status)
                    elif resp.get('result').upper() == "FAILURE":
                        print "CRITICAL: last build end with failure at %s" % date_exec
                        sys.exit(jenkins.critical_status)
                elif status == "Disabled":
                    print "Warning: Job disabled, Not need to check last build"
                    sys.exit(jenkins.warning_status)
                elif status == "Notbuilt":
                    print "CRITICAL: Build was aborted"
                    sys.exit(jenkins.critical_status)
                else:
                    pass
            else:
                print "%s -> JobName not found" % job_name
                sys.exit(jenkins.critical_status)
        elif opt in ("-f", "--file"):
            list_job_file = arg.strip()
            if not os.path.exists(list_job_file):
                print "%s -> File not found" % list_job_file
                sys.exit(-4)
            else:
                with open(list_job_file, 'r') as f:
                    list_job_name = f.read().splitlines()
                jenkins = JenkinsApi()
                success_job = list()
                failed_jobs = list()
                for job_name in list_job_name:
                    if job_name != "":
                        exist, status = jenkins.exist_jobs(job_name.strip().lower())
                        if exist:
                            if status == "Enabled":
                                job_url_rest = jenkins.jenkins_url + "/job/" + urllib.quote(
                                    job_name.strip()) + "/lastBuild/api/json"
                                # print job_url_rest
                                resp = jenkins.get_json_resp(url=job_url_rest)
                                # print resp
                                # timestamp = resp.get('timestamp')
                                # utc time
                                # date_exec = datetime.utcfromtimestamp(float(timestamp) / 1000.).strftime(
                                #     "%Y-%m-%d %H:%M:%S")
                                if resp.get('result').upper() == "SUCCESS":
                                    # print "OK: last build end with success at %s" % date_exec
                                    # sys.exit(jenkins.ok_status)
                                    success_job.append(job_name)
                                elif resp.get('result').upper() == "FAILURE":
                                    # print "CRITICAL: last build end with failure at %s" % date_exec
                                    # sys.exit(jenkins.critical_status)
                                    failed_jobs.append(job_name)
                            elif status == "Disabled":
                                # ignoring disable job
                                print "%s : Disabled job -> Not need to check last build" % job_name
                                # sys.exit(jenkins.warning_status)
                                pass
                            elif status == "Notbuilt":
                                print "%s : is Not buildable job, you need to delete him from this file -> %s" % (
                                job_name, sys.argv[2])
                                sys.exit(jenkins.unknown_status)

                        else:
                            print "-> %s: job not found!" % job_name
                            sys.exit(jenkins.unknown_status)

                if len(failed_jobs) > 0:
                    print "CRITICAL: list failed jobs -> %s" % [job for job in failed_jobs]
                    sys.exit(jenkins.critical_status)
                else:
                    if len(success_job) > 0:
                        print "OK: All jobs are ok %s" % [job for job in success_job]
                        sys.exit(jenkins.ok_status)
        else:
            usage()