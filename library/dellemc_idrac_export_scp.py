#! /usr/bin/python
# _*_ coding: utf-8 _*_

#
# Copyright (c) 2017 Dell Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: dellemc_idrac_export_scp
short_description: Export Server Configuration Profile (SCP) to network share
version_added: "2.3"
description:
    - Export Server Configuration Profile 
options:
    idrac_ip:
        required: False
        description: iDRAC IP Address
        default: None
    idrac_user:
        required: False
        description: iDRAC user name
        default: None
    idrac_pwd:
        required: False
        description: iDRAC user password
        default: None
    idrac_port:
        required: False
        description: iDRAC port
        default: None
    share_name:
        required: True
        description: CIFS or NFS Network share 
    share_user:
        required: True
        description: Network share user in the format user@domain
    share_pwd:
        required: True
        description: Network share user password

requirements: ['omsdk']
author: "anupam.aloke@dell.com"
"""

EXAMPLES = """
---
"""

RETURNS = """
---
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from omsdk.sdkfile import FileOnShare
    from omsdk.sdkcreds import UserCredentials,ProtocolCredentialsFactory
    HAS_OMSDK = True
except ImportError:
    HAS_OMSDK = False


# Export Server Configuration Profile (SCP)
def export_server_config_profile(idrac, module):

    msg = {}
    msg['changed'] = False
    msg['failed'] = False
    err = False

    try:
        scp_file_name = idrac.ipaddr + "_%Y%M%d_scp.xml"
        share_path = module.params['share_name'] + scp_file_name

        myshare = FileOnShare(share_path)
        myshare.addcreds(UserCredentials(module.params['share_user'],
                                         module.params['share_pwd']))
        msg['msg'] = idrac.config_mgr.scp_export(myshare)

        if "Status" in msg['msg'] and msg['msg']['Status'] is not "Success":
            msg['failed'] = True

    except Exception as e:
        err = True
        msg['msg'] = "Error: %s" % str(e)
        msg['failed'] = True

    return msg, err

# Main
def main():

    from ansible.module_utils.dellemc_idrac import iDRACConnection

    module = AnsibleModule (
                 argument_spec = dict (

                     # iDRAC Handle
                     idrac      = dict (required = False, type = 'dict'),

                     # iDRAC credentials
                     idrac_ip   = dict (required = False, default = None, type='str'),
                     idrac_user = dict (required = False, default = None, type='str'),
                     idrac_pwd  = dict (required = False, default = None,
                                        type='str', no_log = True),
                     idrac_port = dict (required = False, default = None, type = 'int'),

                     # Network File Share
                     share_name = dict (required = True, default = None),
                     share_pwd  = dict (required = True, default = None,
                                        no_log = True),
                     share_user = dict (required = True, default = None),
                  ),

                  supports_check_mode = True)

    # Connect to iDRAC
    idrac_conn = iDRACConnection (module)
    idrac = idrac_conn.connect()

    # Export Server Configuration Profile
    msg, err = export_server_config_profile(idrac, module)

    # Disconnect from iDRAC
    idrac_conn.disconnect()

    if err:
        module.fail_json(**msg)
    module.exit_json(**msg)


if __name__ == '__main__':
    main()
