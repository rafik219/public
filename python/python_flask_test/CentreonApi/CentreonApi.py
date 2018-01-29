from flask import Flask
from flask_restplus import Api, Resource

from centreon import Centreon

app = Flask(__name__)
api = Api(app, version='0.1', title='Centreon API', description='Centreon API usage', )

ns = api.namespace('api', description='Get all nagios alerts')

centreon_instance = Centreon()


@ns.route('/get_all_critical_service')
class GetCriticalAlert(Resource):
    """Get Critical Service From Nagios"""

    @ns.doc('Get all critical services',
            responses={
                '200': 'Success',
                '500': 'Internal failure',
            },
            )
    # @ns.marshal_list_with(model)
    # @ns.marshal_with(model)
    def get(self):
        """Get all critical service"""
        all_critical_service = centreon_instance.group_critical_services_by_hosts(
                critical_service=centreon_instance.get_all_critical_service())
        if len(all_critical_service) != 0:
            return all_critical_service, 200
        api.abort(404, "Error during get all critical hosts")


@ns.route('/get_all_critical_service/<string:hostname>')
@ns.param('hostname', description='Host Name')
# @ns.response(404, description='Host not found !')
class GetAllServiceForHost(Resource):
    """Get all supervised service for host"""

    @ns.doc('Get all service status for host',
            responses={
                '200': 'Success',
                '403': 'Host not found on Nagios',
                '500': 'Internal failure',
            },
            )
    def get(self, hostname):
        """Get all services for Host"""
        all_service = centreon_instance.get_all_service_for_host(search_host=hostname)
        if all_service.get('count_ok_service') == 0 \
                and all_service.get('count_cri_service') == 0 \
                and all_service.get('count_unk_service') == 0 \
                and all_service.get('count_war_service') == 0:
            api.abort(404, "Error host '{}' not found !!".format(hostname))
        return all_service, 200


@ns.route('/get_all_hosts')
class GetAllHosts(Resource):
    """Get All Hosts from Nagios with status UP !"""

    @ns.doc('Get all hosts',
            responses={
                '200': 'Success',
                '500': 'Internal failure',
            },
            )
    def get(self):
        """Get all 'UP' hosts from Nagios"""
        all_hosts = centreon_instance.get_all_hosts()
        if len(all_hosts) != 0:
            return all_hosts, 200
        api.abort(404, "Error no host found !!")


@ns.route('/get_all_hosts_by_pop')
class GetAllHostsByPop(Resource):
    """Get All Hosts from Nagios with status UP ! grouped by pop"""

    @ns.doc('Get all hosts grouped by pop',
            responses={
                '200': 'Success',
                '500': 'Internal failure',
            },
            )
    def get(self):
        """Get all 'UP' hosts from Nagios grouped by pop"""
        all_hosts = centreon_instance.group_hosts_by_pop()
        if len(all_hosts) != 0:
            return all_hosts, 200
        api.abort(404, "Error no host found !!")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
