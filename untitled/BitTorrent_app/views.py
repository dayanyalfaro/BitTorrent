import random
import os
import json

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from BitTorrent_app.forms import AddressForm, UploadFileForm
from BitTorrent_app.Logic.client import Client

client = None


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
        dwns = client.download.keys()
    context['DOWNLOADS'] = dwns
    return render(request, '../templates/downloads.html', context)


def uploads(request):
    context = {}
    files = [
        'El Principito.pdf',
        'The Joker.mkv',
        'Bon Jovi - Its my life.mp3',
        'The Lion King.mp4'
    ]
    context['FILES'] = files
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

    data = {'keys': history.keys(), 'history': history}
    if request.is_ajax():
        return JsonResponse(data)


def get_address(request):
    global client
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            path = "./Storage"
            data = form.cleaned_data
            try:
                os.mkdir("./Storage")
            except:
                pass
            client = Client('127.0.0.1', 8888, path, (data['ip'], data['port']))
            return HttpResponseRedirect('/home/')
    else:
        form = AddressForm()
        return render(request, 'input_address.html', {'form': form})


def upload_file(request):
    global client
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['uploaded_file']._name
            size = form.cleaned_data['uploaded_file'].size
            form.save()
            client.copy_file_from_directory(name,size)
        return HttpResponseRedirect('/uplds/')

    else:
        form = UploadFileForm()
        return render(request, 'upload_file.html', {'form': form})
