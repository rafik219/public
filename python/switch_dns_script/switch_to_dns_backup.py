#!/usr/bin/python
# -*- encoding: utf-8

# rbo
# version : 23/11/2016


import datetime
import getopt
import subprocess
import sys
import time
import xmlrpclib


def usage():
    print "------------------------------------------"
    script_name = sys.argv[0]
    print "Usage:"
    print "\t%s -d <dom> -z <zon> -r <opt> -w <wai>\n" \
          "\t%s --domain <dom> --zone <zon> --run <opt> --wait <wai>\n" \
          "\tOu\n" \
          "\t <dom>  : domaine a modifier\n" \
          "\t <zon>  : zone cible\n" \
          "\t <opt>  : ok -> pour lancer la bascule\n" \
          "\t\t: print -> pour afficher des infos" % (script_name, script_name) + "\n" \
          "\t <wai>  : yes -> pour attendre la propagation reseau\n" \
          "\t\t: no -> pour ne pas attendre la propagation reseau"
    print "------------------------------------------"
    sys.exit(-1)


class ApiGandi:
    def __init__(self):
        self._APIKEY = "XXXXXXXXXXXXXXXXXXXXX"
        self._URL = "https://rpc.gandi.net/xmlrpc/"
        self.api = xmlrpclib.ServerProxy(self._URL)

    def get_version(self):
        version = self.api.version.info(self._APIKEY).get('api_version')
        print "api version : %s" % version

    def get_zone_info(self, zone_id):
        return self.api.domain.zone.info(self._APIKEY, zone_id)

    def get_all_domains_list(self):
        return self.api.domain.list(self._APIKEY)

    def get_domain_info(self, domain_name):
        return self.api.domain.info(self._APIKEY, domain_name)

    def get_zone_list(self, zone_name):
        return self.api.domain.zone.list(self._APIKEY, {'name': zone_name})

    def get_domain_list(self, domain_name):
        return self.api.domain.list(self._APIKEY, {'name': domain_name})

    def get_all_zones_list(self):
        return self.api.domain.zone.list(self._APIKEY)

    def set_zone(self, domain_name, zone_id):
        return self.api.domain.zone.set(self._APIKEY, domain_name, zone_id)

    def get_zone_public_ip(self, zone_name):
        # Get all record from the zone
        zone = self.api.domain.zone.list(self._APIKEY, {'name': zone_name})
        zone_id = zone[0].get('id')
        zone_version = zone[0].get('version')
        all_record = self.api.domain.zone.record.list(self._APIKEY, zone_id, zone_version)
        if len(all_record) == 0:
            print "\t => Empty zone !!, %s record found on %s version %s" % (len(all_record), zone_name, zone_version)
            print "\t => Not necessary to switch to the empty zone !!"
            sys.exit(-5)
        else:
            first_record = all_record[0]
            # public ip used in zone
            public_ip_zone = first_record.get('value')
            # print "public ip: %s " % public_ip_zone
            return public_ip_zone

    def display_domain_info(self, domain_info, type='short'):
        domain_name = domain_info.get('fqdn')
        print "\t* Domain information (name : %s) :" % domain_name
        # print "\t----------------------------------------------"
        if type == 'short':
            print "\t\t domaine_name : %s" % domain_name
            print "\t\t domaine_id : %s" % domain_info.get('id')
            print "\t\t attached zone_id : %s" % domain_info.get('zone_id')
        elif type == 'full':
            for info in domain_info:
                obj = domain_info.get(info)
                if isinstance(obj, dict):
                    for elt in obj:
                        print "\t\t\t %s : %s" % (elt, obj.get(elt))
                else:
                    print "\t\t%s : %s" % (info, obj)
        attached_zone_id = domain_info.get('zone_id')
        print "\n\t* Linked zone information (id : %s) :" % attached_zone_id
        # print "\t-----------------------------------------"
        self.display_zone_info(attached_zone_id)

    def display_zone_info(self, zone_id):
        zone_info = self.get_zone_info(zone_id)
        for elt in zone_info.items():
            print "\t\t %s : %s" % (elt[0], elt[1])


if __name__ == "__main__":

    argument = sys.argv[1:]

    if len(argument) < 8:
        usage()

    try:
        opts, args = getopt.getopt(argument, 'd:z:r:w:h', ['domain=', 'zone=', "run=", "wait=", "help="])
    except getopt.GetoptError, ex:
        print str(ex)
        usage()

    for opt, arg in opts:
        if opt in ("-h", '--help'):
            usage()
        elif opt in ("-d", "--domain"):
            DOMAIN_NAME = arg.strip().lower()
        elif opt in ("-z", "--zone"):
            ZONE_NAME = arg.strip().lower()
        elif opt in ("-r", "--run"):
            RUN = arg.lower()
            if RUN not in ("ok", "print"):
                usage()
        elif opt in ("-w", "--wait"):
            WAIT = arg.lower()
            if WAIT not in ("yes", "no"):
                usage()
        else:
            usage()

    if not ZONE_NAME.startswith(DOMAIN_NAME):
        print "\n => Par convention interne a ip-label, le nom de la zone doit commencer par le nom de domaine suivi par _prod ou _backup \n" \
              " => Exemple: \n" \
              "\t\t Domaine: ip-label.net \t\t Zone1: ip-label.net_prod \t Zone2: ip-label.net_backup\n"
        sys.exit(-4)

    # init apiGandi object
    api = ApiGandi()

    # display api version
    api.get_version()

    # Get list of all domains
    domains = api.get_all_domains_list()
    list_domains = [domain.get('fqdn') for domain in domains]

    # check existing domain
    print "Check existing domain:"
    if DOMAIN_NAME in list_domains:
        print "\t=> Success : domain '%s' found!" % DOMAIN_NAME
    else:
        print "\t=> Error : domain '%s' NOT found !" % DOMAIN_NAME
        print "\tExisting Domain:"
        for domain in list_domains:
            print "\t\t -> %s" % domain
        sys.exit(-3)

    # Get first entry for linked zone (public ip)
    old_public_ip_zone = api.get_zone_public_ip(
        (api.get_zone_info((api.get_domain_info(DOMAIN_NAME)).get('zone_id'))).get('name'))
    # print "======> %s" % old_public_ip

    # Get list of all zones:
    print "Check existing zone:"
    zones = api.get_all_zones_list()
    list_zones = [zone.get('name') for zone in zones]

    # check existing zone:
    if ZONE_NAME in list_zones:
        print "\t=> Success : zone %s found !" % ZONE_NAME
    else:
        print "\t=> Error : zone '%s' NOT found !" % ZONE_NAME
        print "\tExisting Zones:"
        for zone in list_zones:
            print "\t\t -> %s" % zone
        sys.exit(-2)

    # Get first entry of zone (public ip)
    new_public_ip_zone = api.get_zone_public_ip(ZONE_NAME)
    # print new_public_ip_zone

    # Get information from domain
    domain_info = api.get_domain_info(DOMAIN_NAME)
    linked_zone_id = domain_info.get('zone_id')
    linked_zone_name = domain_info.get('')
    print "++++++++++"
    print "+ Before +"
    print "++++++++++"
    api.display_domain_info(domain_info, type='short')

    # get information from zone
    # backup_zone = api.domain.zone.list(APIKEY, {'name': ZONE_NAME})
    backup_zone = api.get_zone_list(ZONE_NAME)
    print "------------------------------------------------"
    print "* New zone information (name : %s):" % ZONE_NAME
    print "------------------------------------------------"
    backup_zone_id = backup_zone[0].get('id')
    backup_zone_version = backup_zone[0].get('version')

    api.display_zone_info(backup_zone_id)
    print "------------------------------------------------"
    # linked_zone is the same to new_zone then not need to switch
    if linked_zone_id == backup_zone_id:
        print "\n\n => Not need to switch to the same zone !!\n" \
              "Quit"
        sys, exit(-6)

    # if RUN == "on"
    if RUN == "ok":
        # print "switch to dns backup :"
        print "+++++++++"
        print "+ After +"
        print "+++++++++"
        # if  api.domain.zone.version.set(APIKEY, backup_zone_id, 2):
        #     print "yes"
        # else:
        #     print "no"
        # Set zone backup on domain DOMAIN_NAME
        new_zone = api.set_zone(DOMAIN_NAME, backup_zone_id)
        api.display_domain_info(new_zone, type="short")

        if WAIT == "yes":
            print "----------------------------------------------"
            print "+++++++++++++++++++++++"
            print "+ Wait dns Propagation:"
            print "+++++++++++++++++++++++"
            # wait dns propagation
            print "\n\t* old @ip : %s" % old_public_ip_zone
            print "\t* new @ip : %s" % new_public_ip_zone
            print "\n\t* check with dig command every 120s :"
            start_time = datetime.datetime.now()
            end_time = ""
            while new_public_ip_zone != old_public_ip_zone:
                # init dig command
                # proc = subprocess.Popen(["dig", DOMAIN_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # using google dns resolver
                proc = subprocess.Popen(["dig", DOMAIN_NAME, "@8.8.8.8"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # start process and wait result
                out, err = proc.communicate()
                # Parsing output result
                lines = out.split(';;')

                for elt in lines:
                    if elt.strip().upper().startswith('ANSWER SECTION'):
                        # print Answer section from dig command
                        # print elt
                        sublines = elt.split(u'\n')
                        for i in range(1, (len(sublines) - 2)):
                            # print last entry from answer section
                            print "\t\t %s" % sublines[i]
                        old_public_ip_zone = (sublines[len(sublines) - 3].split(u'\t')[-1]).strip()
                end_time = datetime.datetime.now() - start_time
                # retry after 120s
                time.sleep(120)
            print "\t\n* dns propagation and with success, after : %s !!" % end_time
        else:
            print "\nDone !!\n"
            print "The network propagation delay takes on average 30 minutes ...\n"
            print "To verify use: 'dig %s @8.8.8.8' command\n" % DOMAIN_NAME
            print "\nSUCCESS !!"
            sys.exit(0)
    else:
        print "\nSUCCESS !!"
        sys.exit(0)
    print "\nSUCCESS !!\n"
    sys.exit(0)