from cumulus.util.BaseNameTemplate import BaseNameTemplate


class DefaultNameTemplate(BaseNameTemplate):

    def format(self, name_type, name_text):
        type_string = name_type.__name__

        if type_string is "AutoScalingGroup":
            return "Asg%s" % name_text

        self._throw_not_implemented(type_string)
