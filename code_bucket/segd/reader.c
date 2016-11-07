#include <Python.h>
 
static PyObject* read_header(PyObject* self, PyObject* args)
{
    const char *filename;
    unsigned char header[32];
    int i;
    if (!PyArg_ParseTuple(args, "s", &filename))
        return NULL;
 
    printf("Open %s\n", filename);
    
    FILE *fp;
    fp=fopen(filename, "rb");
    fread(header, 32, 1, fp);
    for(i=0; i<32; i++)
       printf("%d\n", header[i]);
    
    
    
 
    Py_RETURN_NONE;
}
 
static PyMethodDef ReadMethods[] =
{
     {"read_header", read_header, METH_VARARGS, "Reader SEGD file header"},
     {NULL, NULL, 0, NULL}
};
 
PyMODINIT_FUNC
 
initreader(void)
{
     (void) Py_InitModule("reader", ReadMethods);
}