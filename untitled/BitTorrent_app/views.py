import random
import os
import json

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from BitTorrent_app.forms import AddressForm, UploadFileForm
from BitTorrent_app.Logic.client import Client
from BitTorrent_app.Logic.tools import histsize
from untitled.settings import STATICFILES_DIRS


staticfil = STATICFILES_DIRS[0]
# client = Client('127.0.0.1', 8888, staticfil + "/Storage", ("127.0.0.1", 9001))
client = None

def logged_only(func):
    global client
    def wrapper(*args,**kwargs):
        if client == None:
            return HttpResponseRedirect('/')
        return func(*args,**kwargs)
    return wrapper



@logged_only
def home(request):
    return render(request, '../templates/home.html')


@logged_only
def all_files(request):
    global client
    context = {}
    files = []
    names = []
    query = ""
    if client:
        names = client.see_files()

    if request.method == 'GET':
        query = request.GET.get('search_box', "")
        names = [f for f in names if f.find(query) != -1]

    for file in names:
        d = dict()
        d['name'] = file
        d['torrent'] = client.torrent_exists(file)
        files.append(d)
    context['FILES'] = files
    context['query'] = query
    return render(request, '../templates/all_files.html', context)

@logged_only
def downloads(request):
    global client
    start = 0
    if histsize < client.max_dwn:
        start = client.max_dwn - histsize
    context = {}
    dwns = []
    if client:
        for key in range(start, client.max_dwn):
            dwns.append({
                'id':key,
                'name': client.download[key].file_name,
                'width': round(client.download[key].actual_copy/client.download[key].size) * 100,
                'state': client.download[key].state
            })
    context['DOWNLOADS'] = dwns
    return render(request, '../templates/downloads.html', context)

@logged_only
def uploads(request):
    global client
    context = {}
    context['error'] = ''
    files = client.files
    query = ""
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['uploaded_file']._name.find('|') != -1:
                context['error'] = 'File name can not contain |'
            else:
                fd = form.cleaned_data['uploaded_file']
                name = form.cleaned_data['uploaded_file']._name
                size = form.cleaned_data['uploaded_file'].size
                # form.save()
                def copy():
                    try:
                        os.mkdir(staticfil + "/files");
                    except: pass
                    wf = open(staticfil + "/files/" + name, "wb")
                    while 1:
                        data = fd.read(50*1024*1024)
                        if len(data) == 0:
                            break
                        wf.write(data)
                    wf.close()

                    client.copy_file_from_directory(staticfil + "/files/" + name, name)
                copy()

    else:
        query = request.GET.get('search_box', "")
        files = [f for f in files if f.lower().find(query.lower()) != -1]


    form = UploadFileForm()
    context['FILES'] = files
    context['form'] = form
    context['query'] = query
    return render(request, '../templates/uploads.html', context)

@logged_only
def download_file(request, filename):
    if client:
        client.Download(filename)
    return HttpResponseRedirect('/dwns/')

@logged_only
def download_torrent(request, filename):
    if client:
        client.download_torrent(filename)
    return HttpResponseRedirect('/files/')


@logged_only
def update_progress_bar(request):
    global client
    history = {}
    start = 0
    if histsize < client.max_dwn:
        start = client.max_dwn - histsize
    history["range"] = {"first": str(start), "last": str(client.max_dwn)}
    for k in range(start, client.max_dwn):
        dwn = client.download[k]
        data = {"file": dwn.file_name, "size": dwn.size, "copy": dwn.actual_copy, "state": dwn.state}
        history[str(k)] = data

    data = {'history': history}
    if request.is_ajax():
        return JsonResponse(data)


def get_address(request):
    global client
    if (client == None) and request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            path = staticfil + "/Storage"
            data = form.cleaned_data
            try:
                os.mkdir(path)
            except:
                pass
            # client = Client('192.168.43.124', 8888, path, (data['ip'], data['port']))
            client = Client(data['dht_ip'], data['dht_port'], path, (data['ip'], data['port']))
            return HttpResponseRedirect('/home/')
    elif client == None:
        form = AddressForm()
        return render(request, 'input_address.html', {'form': form})
    else:
        return HttpResponseRedirect('/home/')


