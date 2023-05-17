from androguard.core.bytecodes import apk
from collections import deque


def parse_pkg(apk_path,coverage_dict_template):
    a = apk.APK(apk_path)
    androguard_activities = a.get_activities()
    appPackage = a.get_package()
    appActivity = a.get_main_activity()
    permissions = a.get_permissions()
    for activity in androguard_activities:
        activity = activity.replace("..", ".")
        coverage_dict_template.update({activity: {'visited': False}})
    return appPackage,appActivity,permissions


def analyze(apk_path, coverage_dict_template):
    string_activities = '*'
    a = apk.APK(apk_path)
    activities, services, receivers, providers = find_exported_components(a)
    androguard_activities = a.get_activities()
    exported_activities = list()
    for activity in androguard_activities:
        activity = activity.replace("..", ".")
        coverage_dict_template.update({activity: {'visited': False}})
        for act in activities:
            if act in activity:
                exported_activities.append(activity)
    return exported_activities, services, receivers, providers, string_activities, a.package


def find_exported_components(apk):
    activities = list()
    services = list()
    receivers = list()
    providers = list()
    for tag in [
        "activity",
        "activity-alias",
        "service",
        "receiver",
        "provider",
    ]:
        for item in apk.find_tags(tag):
            actions = deque()
            name = item.get(apk._ns("name"), "")
            exported = item.get(apk._ns("exported"), "")
            permission = item.get(apk._ns("permission"), "")

            if name.strip() and exported.lower() != "false":
                to_check = False
                has_actions_in_intent_filter = False
                for intent in item.findall("./intent-filter"):
                    for action in intent.findall("./action"):
                        my_action = action.get(apk._ns("name"), "")
                        if (my_action != 'edu.gatech.m3.emma.COLLECT_COVERAGE') and ('END_COVERAGE' not in
                                                                                    my_action) and ('END_EMMA' not in
                                                                                    my_action):
                            actions.append(my_action)
                            has_actions_in_intent_filter = True

                if exported == "" and has_actions_in_intent_filter:
                    to_check = True

                if exported.lower() == "true":
                    to_check = True

                if to_check:
                    accessible = False
                    if not permission:
                        accessible = True
                    else:
                        detail = apk.get_declared_permissions_details().get(
                            permission
                        )
                        if detail:
                            level = detail["protectionLevel"]
                            if level == "None":
                                level = None
                            if (
                                    level
                                    and (
                                            int(level, 16) == 0x0
                                            or int(level, 16) == 0x1
                                    )
                            ) or not level:
                                accessible = True
                        else:
                            detail = apk.get_details_permissions().get(
                                permission
                            )
                            if detail:
                                level = detail[0].lower()
                                if level == "normal" or level == "dangerous":
                                    accessible = True
                    if accessible:
                        if (tag == "activity") or (tag == "activity-alias"):
                            activities.append(name)
                        elif tag == "service":
                            services.append({'type': 'service', 'name': name, 'action': actions})
                        elif tag == "receiver":
                            receivers.append({'type': 'receiver', 'name': name, 'action': actions})
                        elif tag == "provider":
                            providers.append({'type': 'provider', 'name': name, 'action': actions})
    return activities, services, receivers, providers
