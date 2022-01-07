import json
import pytesseract, base64
import io
from PIL import Image
import requests
from multiprocessing.dummy import Pool
import itertools
import re


def recognizeKVI(data):
    image = bytes_to_image(base64.b64decode(data))
    return pytesseract.image_to_string(image, config='outputbase digits')[:-2]

def bytes_to_image(image_bytes):
    io_bytes = io.BytesIO(image_bytes)
    return Image.open(io_bytes)

def getStudentsByOfferId(_id):
    subjectsTable = getSubjectsTable(_id)
    data = []
    n = 0
    while True:
        postData = {'id':_id, 'last':n}# if n > 0 else {'id':_id}
        r = requests.post('https://vstup.edbo.gov.ua/offer-requests/',
            data=postData,
            headers={
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.67',
                'Referer':'https://vstup.edbo.gov.ua/offer/'+str(_id)})
        try:
            _requests = r.json().get('requests')
        except:
            print('Err')
            continue
        if not _requests:
            _requests = []
        data += _requests
        n+=200
        if len(_requests) > 200 or len(_requests) == 0:
            break
    for i in range(len(data)):
        for z in range(len(data[i]['rss'])):
            if data[i]['rss'][z].get('id') in subjectsTable:
                data[i]['rss'][z]['id'] = subjectsTable[data[i]['rss'][z]['id']]
                data[i]['rss'][z]['b'] = data[i]['rss'][z]['f'][:3]
    return data
    
def getOffersBySpeciality(speciality):
    r = requests.post('https://vstup.edbo.gov.ua/offers-universities/', 
        data = {
            'qualification': '1',
            'education_base': '40',
            'speciality': speciality,
            'region': '',
            'university': '',
            'study_program': '',
            'education_form': '',
            'course': ''
        },
        headers={
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.67',
                'Referer':'https://vstup.edbo.gov.ua/offers/'
        }
    )

    return [i['ids'].split(',') for i in r.json()['universities']]


def getSpecNamesByOfferIds(ids, _spec):
    r = requests.post('https://vstup.edbo.gov.ua/offers-list/', 
        data = {
            'ids':','.join(ids)
        },
        headers={
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.67',
                'Referer':'https://vstup.edbo.gov.ua/offers/?qualification=1&education_base=40&speciality='+str(_spec)
        }
    )
    res = []
    data = r.json()['offers']
    res.append(data[0]['un'])
    res.append([])
    for i in data:
        if not i.get('price'):
            i['price'] = '0'
        res[1].append((i['usid'], i['usn'], i['price']))
    return res


specs = ['011', '012', '013', '014', '014-1', '014-178', '014-179', '014-180', '014-181', '014-182', '014-183', '014-184', '014-185', '014-186', '014-3', '014-4', '014-55', '014-6', '014-7', '014-8', '014-9', '014-10', '014-11', '014-12', '014-13', '014-56', '015', '015-192', '015-193', '015-194', '015-195', '015-196', '015-197', '015-198', '015-199', '015-200', '016', '016-187', '016-188', '016-189', '016-190', '016-191', '017', '021', '022', '022-84', '022-85', '022-86', '022-87', '022-88', '023', '024', '025', '026', '027', '028', '029', '031', '032', '033', '034', '035', '035-37', '035-38', '035-57', '035-58', '035-59', '035-60', '035-61', '035-62', '035-63', '035-64', '035-141', '035-65', '035-66', '035-67', '035-68', '035-69', '035-70', '035-71', '035-72', '035-73', '035-74', '035-75', '035-76', '035-77', '035-78', '035-79', '035-80', '035-81', '035-82', '035-83', '035-146', '035-147', '035-44', '035-148', '035-45', '035-46', '041', '051', '052', '053', '054', '061', '071', '072', '073', '075', '076', '081', '091', '101', '102', '103', '104', '105', '106', '111', '112', '113', '121', '122', '123', '124', '125', '126', '131', '132', '133', '134', '135', '136', '141', '142', '143', '144', '145', '151', '152', '153', '161', '162', '163', '171', '172', '173', '181', '182', '183', '184', '185', '186', '187', '191', '192', '193', '194', '201', '202', '203', '204', '205', '206', '207', '208', '211', '212', '221', '222', '223', '224', '225', '226', '227', '227-167', '227-168', '228', '229', '231', '232', '241', '242', '251', '252', '253', '254', '255', '256', '261', '262', '263', '271', '271-163', '271-164', '271-165', '271-166', '272', '273', '274', '275', '275-47', '275-48', '275-49', '275-50', '281', '291', '292', '293']

n = 1

def parseFacultInfo(spec):
    while True:
        try:
            students = getStudentsByOfferId(spec[0])
            break
        except:
            print('Err2')
            continue
    facultyInfo = {
        "offer_id": int(spec[0]),
        "faculty_name": spec[1],
        "price": int(spec[2]),
        "students": students
    }
    return facultyInfo

def parseOffer(offer_ids, _spec):
    univerSpec = getSpecNamesByOfferIds(offer_ids, _spec)
    r = {
            "spec_num": _spec,
            "univer": univerSpec[0],
            "specs": []
        }
    pool = Pool(5)
    res = pool.map(parseFacultInfo, univerSpec[1])
    r['specs'] = res
    return r


def getBySpec(_spec):
    global n
    offers = getOffersBySpeciality(_spec)
    pool = Pool(10)
    res = pool.starmap(parseOffer, zip(offers, itertools.repeat(_spec)))
    print(str(n)+"/"+str(len(specs))+' '+_spec)
    n+=1
    return res

def getSubjectsTable(offer_id):
    r = requests.get('https://vstup.edbo.gov.ua/offer/'+str(offer_id), 
        headers={
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.67',
        }
    )
    text = r.text
    offers = json.loads(re.search('let offer = (.*?})$', text, re.MULTILINE).group(1))
    return {int(i): offers['os'][i]['sn'] for i in offers['os']}

pool = Pool(10)
res = pool.map(getBySpec, specs)
res = [z for i in res for z in i]

print('Сохранение')
with open('edbo.json', 'w') as f:
    f.write(json.dumps(res, ensure_ascii=False, separators=(',', ':')))
    #json.dump(res, f, ensure_ascii=False)
