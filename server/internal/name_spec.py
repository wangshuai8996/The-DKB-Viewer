import re

def my_regex_for_identifiers(id):
    return id.isidentifier()

def my_regex_for_title(id):
    result = re.search("([a-zA-Z0-9 .,:;_])*", id)
    if (result.group() == id):
        return True
    return False

def my_regex_for_concept_name(name):
    result = re.search("[a-zA-Z]*", name)
    if (result.group() == name):
        return True
    return False

def myRegexForPropertyName(name):
    result = re.search("[a-zA-Z]*", name)
#    print(name+ " "+result.group())
    if (result.group() == name):
        return True
    return False


