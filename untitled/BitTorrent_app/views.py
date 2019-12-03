import random
import os
import json

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from BitTorrent_app.forms import AddressForm
from BitTorrent_app.Logic.client import Client
from django.db import models
from untitled.settings import STATICFILES_DIRS
from django import forms
import random

client = None
rand = None
max_client_connect = 0
clients_connect = []

staticfil = STATICFILES_DIRS[0]

print(staticfil)

class UploadedFile(models.Model):
    global client
    global path
    rand = random.randint(0,200)
    uploaded_file = models.FileField(upload_to=f'./static/files')

class UploadFileForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['uploaded_file',]

def home(request):
    return render(request, '../templates/home.html')


def all_files(request):
    global client
    context = {}
    files = []
    if client:
        names = client.see_files()
    for file in names:
        d = dict()
        d['name'] = file
        d['torrent'] = client.torrent_exists(file)
        files.append(d)
    context['FILES'] = files
    return render(request, '../templates/all_files.html', context)


def downloads(request):
    global client
    context = {}
    dwns = []
    if client:
        for key in client.download.keys():
            dwns.append({'id':key, 'name': client.download[key].file_name})
    context['DOWNLOADS'] = dwns
    return render(request, '../templates/downloads.html', context)


def uploads(request):
    global client
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['uploaded_file']._name
            size = form.cleaned_data['uploaded_file'].size
            form.save()
            client.copy_file_from_directory(staticfil + "/files/" + name, name)
    context = {}
    files = client.files
    form = UploadFileForm()
    context['FILES'] = files
    context['form'] = form
    return render(request, '../templates/uploads.html', context)


def download_file(request, filename):
    if client:
        client.Download(filename)
    return HttpResponseRedirect('/dwns/')


def download_torrent(request, filename):
    if client:
        client.download_torrent(filename)
    return HttpResponseRedirect('/files/')


def cancel_upload(request):
    pass


def update_progress_bar(request):
    with open(client.path + "/history.json", "r") as fd:
        history = json.load(fd)

    data = {'history': history}
    if request.is_ajax():
        return JsonResponse(data)


def get_address(request):
    global client
    global max_client_connect
    global rand
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            path = staticfil + "/Storage"
            data = form.cleaned_data
            try:
                os.mkdir(path)
            except:
                pass
            # client = Client('192.168.43.124', 8888, path, (data['ip'], data['port']))
            client = Client('127.0.0.1', 8888, path, (data['ip'], data['port']))
            max_client_connect += 1
            return HttpResponseRedirect('/home/')
    else:
        form = AddressForm()
        return render(request, 'input_address.html', {'form': form})


