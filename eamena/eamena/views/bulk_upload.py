'''
ARCHES - a program developed to inventory and manage immovable cultural heritage.
Copyright (C) 2013 J. Paul Getty Trust and World Monuments Fund

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
'''
import os
import json
from django import forms
from django.conf import settings
from django.core.management import call_command
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse
import logging

def handle_uploaded_file(f):
    '''the actual file upload happens here, and returns a path to the file
    where it exists on the server'''
    dest_path = os.path.join(settings.BULK_UPLOAD_DIR,str(f))
    with open(dest_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return dest_path

def main(request):
    ''' nothing special here, everything is handled with ajax'''
    
    return render_to_response('bulk-upload.htm',
        {'active_page': 'Bulk Upload'}, # not sure if this is necessary
        context_instance=RequestContext(request) # or this
    )

def validate(request):
    '''this view is designed to be hit with an ajax call that includes the path
    to the spreadsheet on the server, and the resource type for the spreadsheet
    '''
    
    fpath = request.POST['filepath']
    restype = request.POST['restype']

    ## using StringIO we can capture the json path output from the command
    ## this is mocked up but not fully implemented.
    from StringIO import StringIO
    out = StringIO()
    call_command('Excelreader',
        operation='site_dataset',
        source=fpath,
        res_type=restype,
        dest_dir='output.arches',
        stdout = out,
    )
    comm_result = out.getvalue()
    
    ## METHOD 1: load logged messages from logger pass them
    ## as a list of lines to the ajax result.
    ## this method currently in use
    logger = logging.getLogger('excel-reader')
    log = logger.handlers[0].baseFilename
    with open(log,'r') as openlog:
        lines = [l.rstrip() for l in openlog]
    result = {
        'success':True,
        'msg': lines,
    }
    
    ## METHOD 2: get the json directly from the management command
    ## and load it here. not currently in use. I think this may be a
    ## good direction to go, but we'll still have to load from a file
    ## for the easiest method
    
    ## results = json.loads(comm_result)
    
    
    ## delete if any of the tests fail
    if not result['success']:
        os.remove(fpath)

    return HttpResponse(json.dumps(result), content_type="application/json")
    
def upload_spreadsheet(request):
    '''this is the view that handles the file upload ajax call. it includes a
    very simple test for the file format, and returns the file path, name, and
    validity, all of which are used on the front-end.'''
    
    if request.method == 'POST':
        f = request._files['files[]']
        fname = os.path.basename(str(f))
        response_data = {
            'filevalid':True,
            'filename':fname,
            'filepath':'',
        }
        ## simple test for file type; don't upload non-excel files
        if not fname.endswith('.xls') and not fname.endswith('.xlsx'):
            response_data['filevalid'] = False
        else:
            fpath = handle_uploaded_file(f)
            response_data['filepath'] = fpath

        return HttpResponse(json.dumps(response_data), content_type="application/json")