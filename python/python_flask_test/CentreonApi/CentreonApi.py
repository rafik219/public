from flask import Flask, jsonify, render_template

from centreon import Centreon

app = Flask(__name__)

centreon_instance = Centreon()


@app.route('/')
def hello_world():
    return render_template('apidoc.html')


@app.route('/get_all_critical_service')
@app.route('/get_all_critical_service/')
def get_all_critical_service():
    return jsonify(centreon_instance.group_critical_services_by_hosts())


@app.route('/get_all_service_for_host/<string:hostname>')
def get_all_service_for_host(hostname):
    return jsonify(centreon_instance.get_all_service_for_host(search_host=hostname))


@app.route('/get_all_hosts')
@app.route('/get_all_hosts/')
def get_all_hosts():
    return jsonify(centreon_instance.get_all_hosts())


@app.route('/get_grouped_all_hosts')
@app.route('/get_grouped_all_hosts/')
def get_grouped_all_hosts():
    return jsonify(centreon_instance.group_hosts_by_pop())


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
