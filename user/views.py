from django.shortcuts import render, redirect
from django.http.response import HttpResponse
from django.http.response import JsonResponse
from django.contrib import messages
from .forms import UserLoginForm, CreateUserForm
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth.hashers import check_password
import json
import sys
from .models import User, State, Common, Context, Concept, Instance, Attribute, Relation
from django.contrib.auth import authenticate, login, logout
sys.path.append('../')
import DKBlib as DKB

global data
data = []
global link
link = []
global userName
userName = ""


def start(request):
    return render(request, "user/background.html")


def login_page(request):
    """
    process the logging information
    :param request:
    :return:
    """
    global userName
    if request.method == 'POST':
        username = request.POST.get('username')
        password =request.POST.get('password')
        user_set = User.objects.filter(name=username)
        if user_set.count() == 0:
            messages.info(request, 'The account does not exist')
        else:
            user = user_set[0]
            if password != user.password:
                messages.info(request, 'Username OR password is incorrect')
            else:
                userName = username
                return redirect('home')
    context = {}
    return render(request, 'user/background.html', context)


def register(request):
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('name')
            messages.success(request, 'Account was created for ' + username)
            return redirect('login_page')

    context = {'form': form}
    return render(request, 'user/register.html', context)


def home(request):
    """
    after logging in, iterate the contents in the DKB and display them
    :param request:
    :return:
    """
    global data
    global link
    global userName
    # use the prefix to identify a context, use the pid to identify a concept, instance and attribute
    data = []
    link = []
    uname = userName
    dkb = DKB.login('ex3KB', uname)
    try:
        context_list, concept_list, instance_list, relation_list, attribute_list = context_iterate(dkb)
    finally:
        dkb.close()
    for context_dict in context_list:
        data_dict = {'id': context_dict.get("name"),
                     'name': context_dict.get("name"), 'des': context_dict.get("name"),
                     'category': context_dict.get("object").category,
                     'store': context_dict.get("object").store,
                     'symbolSize': context_dict.get("object").symbolSize,
                     'itemStyle': {'color': context_dict.get("object").color},
                     'info': context_dict.get("object").get_info(),
                     'search_path': context_dict.get("object").search_path,
                     'context': context_dict.get("name"), 'attributes': {}}
        data.append(data_dict)
    for concept_dict in concept_list:
        data_dict = {'id': concept_dict.get("pid"), 'name': concept_dict.get("object").name,
                     'des': concept_dict.get("object").name,
                     'category': concept_dict.get("object").category,
                     'store': concept_dict.get("object").store,
                     'symbolSize': concept_dict.get("object").symbolSize,
                     'itemStyle': {'color': concept_dict.get("object").color},
                     'info': concept_dict.get("object").get_info(),
                     'search_path': [], 'context': concept_dict.get("object").context,
                     'attributes': concept_dict.get("object").get_attributes()}
        data.append(data_dict)
    for instance_dict in instance_list:
        data_dict = {'id': instance_dict.get("pid"),
                     'name': instance_dict.get("object").name, 'des': instance_dict.get("object").name,
                     'category': instance_dict.get("object").category,
                     'store': instance_dict.get("object").store,
                     'symbolSize': instance_dict.get("object").symbolSize,
                     'itemStyle': {'color': instance_dict.get("object").color},
                      # the context here for an instance actually stores its concept's pid
                     'info': "", 'search_path': [], 'context': instance_dict.get("object").concept,
                     'attributes': instance_dict.get("object").get_attributes()}
        data.append(data_dict)
    for attribute in attribute_list:
        data_dict = {'id': attribute.id, 'name': attribute.name, 'des': attribute.value,
                     'category': attribute.category, 'store': attribute.store,
                     'symbolSize': attribute.symbolSize, 'itemStyle': {'color': attribute.color}, 'info': "",
                     'search_path': [], 'context': "", 'attributes': {}}
        data.append(data_dict)
    for relation in relation_list:
        link.append(relation.get_link())

    return render(request, 'user/login_detail.html', {
        'state_name': json.dumps(get_state_name(userName)),
        'userName': json.dumps(userName),
        'data': json.dumps(data),
        'link': json.dumps(link)
    })


def get_state_name(username):
    """
    get state name from the sql database
    :param username:
    :return:
    """
    state_name = []
    state_set = State.objects.filter(user_name=username)
    if state_set.count() != 0:
        for state in state_set:
            state_name.append({'state': state.name, 'page': state.page})
    print(state_name)
    return state_name


def gohome(request):
    """
    entering the home page
    :param request:
    :return:
    """
    global data
    global link
    global userName
    if request.method == 'GET':
        return render(request, 'user/login_detail.html', {
            'state_name': json.dumps(get_state_name(userName)),
            'userName': json.dumps(userName),
            'data': json.dumps(data),
            'link': json.dumps(link)
        })


def context(request):
    """
    entering a context page
    :param request:
    :return:
    """
    global data
    global link
    global userName
    context_data = []
    context_link = []
    if request.method == 'GET':
        context_name = request.GET.get('context_name')
        context_data, context_link = find_context(context_name)
        return render(request, 'user/context_page.html', {
            'state_name': json.dumps(get_state_name(userName)),
            'userName': json.dumps(userName),
            'data': json.dumps(context_data),
            'link': json.dumps(context_link)
        })
    else:
        return render(request, 'user/login_detail.html', {
            'state_name': json.dumps(get_state_name(userName)),
            'userName': json.dumps(userName),
            'data': json.dumps(data),
            'link': json.dumps(link)
        })


def find_context(context_name):
    """
    find the concepts and instances in a context
    """
    global data
    global link
    print(link)
    context_data = []
    context_link = []
    mark = [context_name]
    while len(mark) > 0:
        current = mark.pop()
        element = findNode(current)
        element['category'] = element['store']
        context_data.append(element)
        # if the node is an attribute, stop here, because it has no child
        if len(current.split(":")) > 4:
            continue
        for line in link:
            if line.get("source") == current:
                target = findNode(line.get("target"))
                # the links between contexts are excluded, the links between concepts added
                if target['store'] != 0:
                    context_link.append(line)
                # only the child of concept will be added (Otherwise the subclass concept will be added)
                if target['store'] > element['store']:
                    mark.append(line.get("target"))
    return context_data, context_link


def concept(request):
    global data
    global link
    global userName
    concept_data = []
    concept_link = []
    if request.method == 'GET':
        concept_name = request.GET.get('concept_name')
        context_name = request.GET.get('context_name')
        concept_data, concept_link = find_concept(concept_name, context_name)
        return render(request, 'user/concept_page.html', {
            'state_name': json.dumps(get_state_name(userName)),
            'userName': json.dumps(userName),
            'data': json.dumps(concept_data),
            'link': json.dumps(concept_link)
        })
    else:
        return render(request, 'user/login_detail.html', {
            'state_name': json.dumps(get_state_name(userName)),
            'userName': json.dumps(userName),
            'data': json.dumps(data),
            'link': json.dumps(link)
        })


def find_concept(concept_name, context_name):
    """
    to find a concept's context and the instances of it.
    """
    global data
    global link
    concept_data = []
    concept_link = []
    # the elements in mark is the name (String type)
    mark = [concept_name]
    while len(mark) > 0:
        current = mark.pop()
        element = findNode(current)
        element['category'] = element['store']
        concept_data.append(element)
        # # if the node is an attribute, stop here, because it has no child
        if len(current.split(":")) > 4:
            continue
        for line in link:
            if line.get("source") == current:
                target = findNode(line.get("target"))
                # the links between contexts are excluded, the links between concepts added
                if target['store'] != 0:
                    concept_link.append(line)
                # only the child of concept will be added (Otherwise the subclass concept will be added)
                if target['store'] > element['store']:
                    mark.append(line.get("target"))
    context_tmp = findNode(context_name)
    concept_data.append(context_tmp)
    concept_link.append({'source': context_name, 'target': concept_name, "lineStyle": {'type': 'solid'}})
    return concept_data, concept_link


def findNode(node_id):
    global data
    for element in data:
        if element.get('id') == node_id:
            # if add this line, the global variable will be changed
            # element['category'] = element.get('store')
            return element


def context_iterate(dkb):
    context_list = []
    concept_list = []
    instance_list = []
    relation_list = []
    attribute_list = []
    dkb_status = dkb.status()
    contexts = dkb_status.get("contexts_available")
    # analyze each context
    for context in contexts:
        dkb.enter(context, 'R')
        sts = dkb.context_status()
        concepts = list(sts.get("concepts").keys())
        instances = list(sts.get("instances").keys())
        search_path = sts.get("search_path")
        context_obj = Context(name=sts.get("prefix"), pid=sts.get("identifier"), search_path=search_path,
                              concepts=concepts, instances=instances, mode=sts.get("mode"),
                              owner=sts.get("owner"), users=sts.get("users"), state=sts.get("state"),
                              title=sts.get("title"))
        context_list.append({"name": context, "object": context_obj})
        for sc in search_path:
            relation = Relation(source=context_obj.name, target=sc, relationship="dashed")
            relation_list.append(relation)
        # iterate the concepts inside
        concept_temp, re1, attr1 = concept_iterate(dkb=dkb, context=context, concepts=concepts)
        concept_list += concept_temp
        relation_list += re1
        attribute_list += attr1
        # iterate the instances inside
        instance_temp, re2, attr2 = instance_iterate(dkb=dkb, context=context, instances=instances, concept_list=concept_list)
        instance_list += instance_temp
        relation_list += re2
        attribute_list += attr2
        dkb.leave()

    return context_list, concept_list, instance_list, relation_list, attribute_list


def concept_iterate(dkb, context, concepts):
    ###
    # context：the name of the context
    # concepts: the name list of the concepts
    ###
    concept_list = []
    relation_list = []
    attribute_list = []
    for concept in concepts:
        attributes = []
        try:
            sts = dkb.get(context + ":" + concept)
        except:
            continue
        specialise = sts.get("specialises")
        concept_obj = Concept(name=sts.get("name"), pid=sts.get("pid"), description=sts.get("description"),
                              mutability=sts.get("mutability"), state=sts.get("state"),
                              translation=sts.get("translation"), timestamp=sts.get("timestamp"),
                              specialise=specialise, attributes=attributes, context=sts.get("prefix"))
        for key, value in sts.get("required").items():
            attributes.append(Attribute(key=key, value=value, attribute_of=concept_obj.pid))
        for key, value in sts.get("recommended").items():
            attributes.append(Attribute(key=key, value=value, attribute_of=concept_obj.pid))
        for key, value in sts.get("optional").items():
            attributes.append(Attribute(key=key, value=value, attribute_of=concept_obj.pid))
        concept_obj.attributes = attributes
        concept_list.append({"pid": concept_obj.pid, "object": concept_obj})
        relation_list.append(Relation(source=concept_obj.context, target=concept_obj.pid, relationship="solid"))
        # currently, we don't display the attribute of concepts
        # for item in attributes:
        #     relation_list.append(Relation(source=concept_obj.pid, target=item.name, relationship=2))
        # the parent concept returned is in different type
        if specialise is not None and specialise != [] and specialise != '':
            if isinstance(specialise, str):
                context_temp = specialise.split(':')[1]
                if context_temp == concept_obj.context:
                    relation_list.append(Relation(source=specialise, target=concept_obj.pid, relationship="dotted"))
            else:
                context_temp = specialise[0].split(':')[1]
                if context_temp == concept_obj.context:
                    relation_list.append(Relation(source=specialise[0], target=concept_obj.pid, relationship="dotted"))
        # attribute_list += attributes
    return concept_list, relation_list, attribute_list


def instance_iterate(dkb, context, instances, concept_list):
    instance_list = []
    relation_list = []
    attribute_list = []
    for instance in instances:
        attributes = []
        fixed = ["name", "pid", "prefix", "state", "timestamp", "instance_of", "mutability"]
        sts = dkb.get(context + ":" + instance)
        instance_obj = Instance(name=sts.get("name"), pid=sts.get("pid"), context=sts.get("prefix"),
                                concept=sts.get("instance_of"), mutability=sts.get("mutability"),
                                state=sts.get("state"))
        instance_list.append({"pid": instance_obj.pid, "object": instance_obj})
        relation_list.append(Relation(source=instance_obj.concept, target=instance_obj.pid, relationship="solid"))
        # attribute information
        for key in sts.keys():
            if key not in fixed:
                attribute = Attribute(key=key, value=sts.get(key), attribute_of=instance_obj.pid)
                attributes.append(attribute)
                relation_list.append(Relation(source=instance_obj.pid, target=attribute.id, relationship="solid"))
        instance_obj.attributes = attributes
        attribute_list += attributes
    return instance_list, relation_list, attribute_list


def save_state(request):
    """
    save a state into the SQL database
    :param request:
    :return:
    """
    if request.method == 'POST':
        info = json.loads(request.body.decode('utf-8'))
        username = info['username']
        state = info['state']
        page = info['page']
        save_data = info['data']
        save_link = info['link']

        try:
            State.objects.get_or_create(name=state, user_name=username, page=page, data=json.dumps(save_data),
                                        link=json.dumps(save_link))
        except Exception:
            print("something is wrong")
            return JsonResponse({'code': 0, 'state_name': get_state_name(username)})
        else:
            return JsonResponse({'code': 1, 'state_name': get_state_name(username)})

    else:
        return render(request, "user/background.html")


def del_state(request):
    """
    delete a state from the sql database
    :param request:
    :return:
    """
    if request.method == 'GET':
        username = request.GET.get('username')
        state = request.GET.get('state')
        print(username)
        print(state)
        try:
            s = State.objects.filter(user_name=username, name=state).first()
            s.delete()
            return JsonResponse({'code': 1, 'state_name': get_state_name(state)})
        except:
            return JsonResponse({'code': 0, 'state_name': get_state_name(state)})
    else:
        return render(request, "user/background.html")


def go_state(request):
    """
    recover the state
    :param request:
    :return:
    """
    if request.method == 'GET':
        username = request.GET.get('username')
        state = request.GET.get('state')
        page = request.GET.get('page')
        state_set = State.objects.filter(user_name=username, name=state)
        if state_set.count() != 0:
            s = state_set[0]
            state_data = s.data
            state_link = s.link
            print(json.loads(state_data))
            if page == 'context':
                return render(request, 'user/context_page.html', {
                    'state_name': json.dumps(get_state_name(username)),
                    'userName': json.dumps(username),
                    'data': state_data,
                    'link': state_link
                })
            elif page == "concept":
                return render(request, 'user/concept_page.html', {
                    'state_name': json.dumps(get_state_name(username)),
                    'userName': json.dumps(username),
                    'data': state_data,
                    'link': state_link
                })
            else:
                return render(request, 'user/login_detail.html', {
                    'state_name': json.dumps(get_state_name(username)),
                    'userName': json.dumps(username),
                    'data': state_data,
                    'link': state_link
                })
        else:
            return render(request, "user/background.html")
    else:
        return render(request, "user/background.html")


def logout_user(request):
    logout(request)
    return redirect('login_page')

