import cPickle as pickle
import os

from pyspark import SparkConf, SparkContext, StorageLevel

from pprint import pprint


def convObjectToBytesPickle(currentObject):
    """Convert a python object to byte array using pickle

    Args:
        currentObject : a Python object that can be pickled
    Return:
        sequence of bytes
    """

    bObject = pickle.dumps(currentObject)

    return bObject


def convBytesToObjectPickle(bObject):
    """Convert a byte sequence to object using pickle

    Args:
        bObject : serialized object

    """

    return pickle.loads(str(bObject))


if __name__ == '__main__':

    conf = (SparkConf()
            .setMaster("local")
            .setAppName("demo avro"))

    sc = SparkContext(conf=conf)

    fileAvroOut = os.path.join('./test.avro')

    # ------------------------------------
    # -- let's build an example  record --
    # ------------------------------------

    firstmap = {
        'field1': 1.0,
        'field2': 2
    }

    record = {
        'name1': 'firstmap',
        'raw1': firstmap,
        'name2': 'nothing',
        'raw2': [],
        'name3': 'string',
        'raw3': 'a string example'
    }

    # ------------------------------------
    # -- let's pack data                --
    # ------------------------------------

    inputData = record.copy()

    for k in ['raw1', 'raw2', 'raw3']:
        inputData[k] = bytearray(convObjectToBytesPickle(inputData[k]))

    # ------------------------------------
    # -- write data to avro             --
    # ------------------------------------

    avroRdd = sc.parallelize([inputData, inputData])

    pathToScheme1 = './src/main/resources/scheme1.avsc'

    conf = {"avro.schema.output.key": open(pathToScheme1, 'r').read()}

    avroRdd.map(lambda x: (x, None)).saveAsNewAPIHadoopFile(
        fileAvroOut,
        "org.apache.avro.mapreduce.AvroKeyOutputFormat",
        "org.apache.avro.mapred.AvroKey",
        "org.apache.hadoop.io.NullWritable",
        keyConverter="irt.pythonconverters.Scheme1ToAvroKeyConverter",
        conf=conf)

    # ------------------------------------
    # -- read data from avro            --
    # ------------------------------------

    avroRdd2 = sc.newAPIHadoopFile(
        fileAvroOut,
        "org.apache.avro.mapreduce.AvroKeyInputFormat",
        "org.apache.avro.mapred.AvroKey",
        "org.apache.hadoop.io.NullWritable",
        keyConverter="irt.pythonconverters.AvroWrapperToJavaConverter",
        conf=conf)

    crudeData = avroRdd2.collect()

    output = crudeData[0][0]

    for k in ['raw1', 'raw2', 'raw3']:
        output[k] = convBytesToObjectPickle(output[k])

    print 80 * '#'
    print "input Record"
    print 80 * '#'
    pprint(record)

    print 80 * '#'
    print "output Record"
    print 80 * '#'

    pprint(output)

    sc.stop()


# ################################################################################
# input Record
# ################################################################################
# {'name1': 'firstmap',
#  'name2': 'nothing',
#  'name3': 'string',
#  'raw1': {'field1': 1.0, 'field2': 2},
#  'raw2': [],
#  'raw3': 'a string example'}
# ################################################################################
# output Record
# ################################################################################
# {u'name1': u'firstmap',
#  u'name2': u'nothing',
#  u'name3': u'string',
#  u'raw1': {'field1': 1.0, 'field2': 2},
#  u'raw2': [],
#  u'raw3': 'a string example'}
