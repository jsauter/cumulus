from troposphere import (
    Ref,
    Join,
)


def user_data_for_cfn_init(launch_config_name, asg_name, configsets):
    """
    :return: A troposphere Join object that contains userdata for use with cfn-init
    :param configsets: The single 'key' value set in the cfn-init Metadata parameter: cloudformation.InitConfigSets
    :type asg_name: String name of the ASG cloudformation resource
    :type launch_config_name: String name of the launch config cloudformation resource
    """
    default_userdata_asg_signal = (
        Join('',
             [
                 "<powershell>\n",
                 "& ", "$env:ProgramFiles\Amazon\cfn-bootstrap\cfn-init.exe",
                 "         --stack ", Ref("AWS::StackName"),
                 "         --resource ", launch_config_name,
                 "         --configsets %s " % configsets,
                 "         --region ", Ref("AWS::Region"), "\n",
                 "# Signal the ASG we are ready\n",
                 "&", "$env:ProgramFiles\Amazon\cfn-signal",
                 " -e ",
                 " $LastExitCode",
                 "    --resource %s" % asg_name,
                 "    --stack ", Ref("AWS::StackName"),
                 "    --region ", Ref("AWS::Region"),
                 "\n",
                 "</powershell>"
             ]))
    return default_userdata_asg_signal
