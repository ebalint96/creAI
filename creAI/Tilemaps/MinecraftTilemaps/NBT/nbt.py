from __future__ import print_function

import sys
import struct
import gzip
import io

import numpy as np

import time

class TAG(object):
    #__slots__ = ('_name','_payload')

    def __init__(self, name="", payload=0):
        self.name = name
        self.payload = payload

    _name = None
    _payload = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = str(new_name)

    @property
    def payload(self):
        return self._payload
    
    @payload.setter
    def payload(self, new_payload):
        self._payload = self.payload_type(new_payload)

    def __str__(self):
        return printNBTTree(self)

    @classmethod
    def load_payload(cls, raw_data, data_offset):
        data = raw_data[data_offset[0]:]
        payload = None
        (payload,) = cls.payload_format.unpack_from(data)
        self = cls(payload=payload)
        data_offset[0] += self.payload_format.size

        return self

    def write_tag(self, buffer_):
        buffer_.write(bytes([self.tag_type]))

    def write_name(self, buffer_):
        if self.name is not None:
            encoded = self.name.encode('utf-8')
            buffer_.write(struct.pack(">h%ds" % (len(encoded),), len(encoded), encoded))

    def write_payload(self, buffer_):
        buffer_.write(self.payload_format.pack(self.payload))

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12

class TAG_Byte(TAG):
    tag_type = TAG_BYTE
    payload_type = int
    payload_format = struct.Struct(">B")

class TAG_Short(TAG):
    tag_type = TAG_SHORT
    payload_type = int
    payload_format = struct.Struct(">h")

class TAG_Int(TAG):
    tag_type = TAG_INT
    payload_type = int
    payload_format = struct.Struct(">i")

class TAG_Long(TAG):
    tag_type = TAG_LONG
    payload_type = int
    payload_format = struct.Struct(">q")

class TAG_Float(TAG):
    tag_type = TAG_FLOAT
    payload_type = float
    payload_format = struct.Struct(">f")

class TAG_Double(TAG):
    tag_type = TAG_DOUBLE
    payload_type = float
    payload_format = struct.Struct(">d")

#class TAG_Array(TAG):
#
#    def __init__(self, payload=None, name=""):
#        if payload is None:
#            self.payload = []
#        else:
#            self.payload = payload
#        self.name = name
#
#    @classmethod
#    def load_payload(cls, raw_data, data_offset):
#        self = cls()
#        size = TAG_Int.load_payload(raw_data, data_offset).payload
#        for i in range(size):
#            element =  tag_type_IDs_to_classes[self.element_type].load_payload(raw_data, data_offset)
#            self._payload.append(element)
#        return self
#
#    def payload_type(self, payload):
#        for item in payload:
#            if item is not isinstance(item, tag_type_IDs_to_classes[self.element_type]):
#                raise TypeError("TAG_Byte_Array's elements are not integers!")
#        return list(payload)
#
#    def __getitem__(self, index):
#        return self.payload[index]

#class TAG_Byte_Array(TAG_Array):
#    tag_type = TAG_BYTE_ARRAY
#    element_type = TAG_BYTE

class TAG_Array(TAG):

    def __init__(self, payload=None, name=""):
        if payload is None:
            payload = np.zeros(0, self.dtype)
        self.name = name
        self.payload = payload

    def payload_type(self, payload):
        return np.array(payload, self.dtype)

    @classmethod
    def load_payload(cls, raw_data, data_offset):
        data = raw_data[data_offset[0]:]
        (string_len,) = TAG_Int.payload_format.unpack_from(data)
        payload = np.fromstring(data[4:string_len * cls.dtype.itemsize + 4], cls.dtype)
        self = cls(payload)
        data_offset[0] += string_len * cls.dtype.itemsize + 4
        return self

    def write_payload(self, buffer_):
        payload_str = self.payload.tostring()
        buffer_.write(struct.pack(">I%ds" % (len(payload_str),), self.payload.size, payload_str))

#class TAG_Byte_Array(TAG):
#    tag_type = TAG_BYTE_ARRAY
#    element_type = TAG_BYTE
#
#    @classmethod
#    def load_payload(cls, raw_data, data_offset):
#        self = cls()
#        size = TAG_Int.load_payload(raw_data, data_offset).payload
#        payload = raw_data[data_offset : data_offset + tag_type_IDs_to_classes[self.element_type].payload_format.size * size]
#        data_offset += tag_type_IDs_to_classes[self.element_type].payload_format.size * size
#        self = cls(payload=payload)
#        return self
#
#    def payload_type(self, payload):
#        #for item in payload:
#        #    if item is not isinstance(item, tag_type_IDs_to_classes[self.element_type]):
#        #        raise TypeError("TAG_Byte_Array's elements are not integers!")
#        return payload
#
#    def __getitem__(self, index):
#        return tag_type_IDs_to_classes[self.element_type].load_payload(
#            self.payload[index * tag_type_IDs_to_classes[self.element_type].payload_format.size: (index + 1) * tag_type_IDs_to_classes[self.element_type].payload_format.size],
#            [0]
#            )
class TAG_Byte_Array(TAG_Array):
    tag_type = TAG_BYTE_ARRAY
    dtype = np.dtype('uint8')

class TAG_Int_Array(TAG_Array):
    tag_type = TAG_INT_ARRAY
    dtype = np.dtype('>u4')

class TAG_Long_Array(TAG_Array):
    tag_type = TAG_LONG_ARRAY
    dtype = np.dtype('>q')

class TAG_String(TAG):
    tag_type = TAG_STRING

    @classmethod
    def load_payload(cls, raw_data, data_offset):
        payload = load_string(raw_data, data_offset)
        self = cls(payload = payload)
        return self

    def payload_type(self, payload):
        if isinstance(payload, str):
            return payload
        else:
            return payload.decode('utf-8')

    def write_payload(self, buffer_):
        encoded = self.payload.encode('utf-8')
        buffer_.write(struct.pack(">h%ds" % (len(encoded),), len(encoded), encoded))

def load_string(raw_data, data_offset):
    data = raw_data[data_offset[0]:]
    string_length_format = struct.Struct(">H")
    (string_length,) = string_length_format.unpack_from(data)
    data_offset[0] += 2 + string_length
    return data[2:2 + string_length].decode('utf-8')

class TAG_Compound(TAG):
    tag_type = TAG_COMPOUND

    def __init__(self, payload=None, name=""):
        if payload is None:
            self.payload = []
        else:
            self.payload = payload
        self.name = name

    @classmethod
    def load_payload(cls, raw_data, data_offset):
        self = cls()
        while data_offset[0] < len(raw_data):
            tag_type = raw_data[data_offset[0]]

            data_offset[0] += 1

            if tag_type == 0:
                break
            name = load_string(raw_data, data_offset)
            tag = tag_type_IDs_to_classes[tag_type].load_payload(raw_data, data_offset)
            tag.name = name
            self._payload.append(tag)
        
        return self

    def payload_type(self, payload):
        for t in payload:
            if not isinstance(t, TAG):
                print(type(t))
                print(TAG)
                raise TypeError("TAG_Compound's payload is not TAG element!")
        return list(payload)

    def __getitem__(self, name):
        matching_tag = None
        for tag in self.payload:
            if tag.name == name:
                matching_tag = tag
                break
        if matching_tag is None:
            raise KeyError("Tag with name \"{}\" not found in payload".format(str(name)))
        else:
            return matching_tag

    def write_payload(self, buffer_):
        for tag in self.payload:
            tag.write_tag(buffer_)
            tag.write_name(buffer_)
            tag.write_payload(buffer_)

        buffer_.write(bytes([TAG_END]))

class TAG_List(TAG):
    tag_type = TAG_LIST

    def __init__(self, payload=None, name=""):
        if payload is None:
            self.payload = []
        else:
            self.payload = payload
        self.name = name
    
    @classmethod
    def load_payload(cls, raw_data, data_offset):
        self = cls()
        self.element_type = TAG_Byte.load_payload(raw_data, data_offset).payload
        size = TAG_Int.load_payload(raw_data, data_offset).payload
        for i in range(size):
            element =  tag_type_IDs_to_classes[self.element_type].load_payload(raw_data, data_offset)
            self._payload.append(element)
        return self

    def payload_type(self, payload):
        for item in payload:
            if not isinstance(item, tag_type_IDs_to_classes[self.element_type]):
                raise TypeError("TAG_Byte_Array's elements are not integers!")
        return list(payload)

    def __getitem__(self, index):
        return self.payload[index]

    def write_payload(self, buffer_):
        buffer_.write(bytes([self.element_type]))
        buffer_.write(TAG_Int.payload_format.pack(len(self.payload)))
        for i in self.payload:
            i.write_payload(buffer_)


tag_type_IDs_to_classes = {}
tag_classes = (TAG_Byte, TAG_Short, TAG_Int, TAG_Long, TAG_Float, TAG_Double, TAG_Byte_Array, TAG_Int_Array, TAG_Long_Array, TAG_String, TAG_Compound, TAG_List)
for class_name in tag_classes:
    tag_type_IDs_to_classes[class_name.tag_type] = class_name

def printNBTTree(root_tag, level=0):
    output_string = ""
    if root_tag.tag_type in [TAG_COMPOUND, TAG_BYTE_ARRAY, TAG_INT_ARRAY, TAG_LONG_ARRAY, TAG_LIST]:
        output_string += "  "*level + "+ [{}] {} :\n".format(str(root_tag.__class__.__name__),root_tag.name)
        for tag in root_tag.payload:
            output_string += printNBTTree(tag, level+1)
    elif root_tag.tag_type in [TAG_BYTE]:
        output_string += "  "*level + "- [{}] {} : {}\n".format(str(root_tag.__class__.__name__),root_tag.name,root_tag.payload)
    else:
        output_string += "  "*level + "- [{}] {} : {}\n".format(str(root_tag.__class__.__name__),root_tag.name,root_tag.payload)
    return output_string

def load(file_name=None, raw_data=None):
    if file_name is not None:
        with gzip.open(file_name,"rb") as file:
            raw_data = file.read()
            if isinstance(raw_data, str):
                raw_data = np.fromstring(raw_data, 'uint8')
            data_offset = [1]
            tag_name = load_string(raw_data, data_offset)
            tag = TAG_Compound.load_payload(raw_data, data_offset)
            tag.name = tag_name
        return tag
    elif raw_data is not None:
        raw_data = gzip.GzipFile(fileobj=io.BytesIO(raw_data)).read()
        if isinstance(raw_data, str):
            raw_data = np.fromstring(raw_data, 'uint8')
        data_offset = [1]
        tag_name = load_string(raw_data, data_offset)
        tag = TAG_Compound.load_payload(raw_data, data_offset)
        tag.name = tag_name
        return tag
    else:
        return None

def save(root_tag, file_name):
    if root_tag.name is None:
        root_tag.name = ""

    buffer_ = io.BytesIO()
    root_tag.write_tag(buffer_)
    root_tag.write_name(buffer_)
    root_tag.write_payload(buffer_)
    data = buffer_.getvalue()

    gzio = io.BytesIO()
    gz = gzip.GzipFile(fileobj=gzio, mode='wb')
    gz.write(data)
    gz.close()
    data = gzio.getvalue()

    f = open(file_name, "wb")
    f.write(data)



def main():
    tag = load(sys.argv[1])
    print(tag["BlockData"][0:32])
    

if __name__ == '__main__':
    main()