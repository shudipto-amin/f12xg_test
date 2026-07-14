import numpy as np
import itertools

def grab_tensor_from_def(outfile, tensor_name, get_all=False):
    '''Read tensor `tensor_name` from a given `outfile` in which 
    the tensor is printed via FORTRAN script.
    ** Note: this only works specifically for reduced 
    3D arrays as printed out by FORTRAN script, where ij are combined into 1 index,
    as is kl. **

    Arguments:
        outfile: <str> path to output file
        tensor_name: <str> name of tensor as printed out in FORTRAN script
        get_all: <bool> if true, then get a list of all matches. If False, get only last match
    Returns:
        tensor: <np.3darray> the tensor in reduced dimensions, nx, ny, nz
    '''
    with open(outfile, 'r') as inp:
        read = False
        iterator = enumerate(inp)
        tensors = []
        for n, line in iterator:
            if f'BEGIN TENSOR PRINT: {tensor_name}' in line:
                read = True
                _, line = next(iterator)
                dims = line.lstrip('dims: ').split()
                nx, ny, nz = [int(d) for d in dims]
                
                tensor = np.zeros((nz, ny, nx))
                continue
            
            if 'END TENSOR PRINT' in line:
                read = False

            if read:
                words = line.split()
                x, y, z = [int(c)-1 for c in words[:-1]]
                val = float(words[-1])
                tensor[z, y, x] = val
                if get_all:
                    tensors.append(tensor)

    if get_all:
        return tensors
    else:
        return tensor

def grab_tensor_from_std(outfile, tensor_name):
    '''Read tensor `tensor_name` from a given `outfile` in which 
    the tensor is printed via C++ script, using the command:
    
    `T[ContextName + "::<tensor_name>"]->Output(xout);`

    Unlike the FORTRAN tensor grabber, this should in principle 
    work for tensors of any dimensions (untested)

    Arguments:
        outfile: <str> path to output file
        tensor_name: <str> name of tensor as printed out in C++ script. E.g. `VF[mnij]`

    Returns:
        tensor: <numpy.ndarray> the tensor in full.
    '''
    def get_properties(line):
        dim_string = line.split('dim: (')[1].split(') sym:')[0]
        dims = [int(x) for x in dim_string.split('x')]
        return dims
        
    def get_block_data(line):
        index_string = line.split('[')[1].split(']')[0]
        indices = []
        for ind in index_string.split():
            try:
                indices.append(int(ind))
            except ValueError:
                indices.append(ind)
        return indices
        
    def get_matrix_data(iterator, indices, tensor):
        for _, line in iterator:
            values_str = line.split()
            try:
                i_ind = int(values_str[0])
                #print(i_ind)
            except (ValueError, IndexError) as e:
                break
            values = [float(x) for x in values_str[1:]]

            slices = (i_ind, Ellipsis,) + tuple(indices[2:])
            tensor[slices] = values
        
    with open(outfile, 'r') as inp:
        read_properties = False
        last_block = False
        iterator = enumerate(inp)
        for n, line in iterator:
            if 'Dump of tensor' in line and tensor_name in line:
                n, line = next(iterator)
                dims = get_properties(line)
                #print(dims) 
                tensor = np.zeros(dims)
                read_properties = True
                
            if read_properties and line.startswith(' Block'):
                indices = get_block_data(line)
                #print(indices)
                #next(iterator)
                next(iterator)
                get_matrix_data(iterator, indices, tensor)

                if (np.array(indices[2:]) == np.array(dims[2:]) - 1).all():
                    break
                
    return tensor

def get_Vplusminus(def_tensor):
    '''Compute V_plus and V_minus from FORTRAN tensor'''
    V_plus = 0.5 * (def_tensor[0,:,:] + def_tensor[1,:,:])
    V_minus = 0.5 * (def_tensor[0,:,:] - def_tensor[1,:,:])
    return V_plus, V_minus
    
def convert_to_full(def_tensor, shape):
    '''Convert FORTRAN tensor to full tensor, in the same shape as that of C++ output.

    Arguments:
        def_tensor: <numpy.3darray> as returned by `grab_tensor_from_def()`
        shape: <list-like> the shape of the resulting tensor, as obtained from `numpy.shape` of the 
            full tensor obtained from C++ code.

    returns: <numpy.ndarray> the full tensor
    '''
    full_tensor = np.zeros(shape)
    Vp, Vm = get_Vplusminus(def_tensor)
    
    M = 0
    for ij in range(shape[0]):
        N = 0
        for kl in range(shape[2]):
            #print(m, n, ij, kl)
            if Vp[ij, kl]:
                full_tensor[ij, ij, kl, kl] = Vp[ij, kl]
            #else:
            #    full_tensor[ij, ij, kl, kl] = 10*ij + kl
            N += 1
        M += 1
    
    for i in range(shape[0]):
        for j in range(i):
            NN = N
            for k in range(shape[2]):
                for l in range(k):
                    #if Vp[M, NN]:
                    full_tensor[i, j, k, l] = Vp[M, NN]
                    full_tensor[j, i, l, k] = Vp[M, NN]
                    #else:
                    #    full_tensor[i, j, k, l] = 10*M + NN
                    full_tensor[i, j, l, k] = Vm[M, NN]
                    full_tensor[j, i, k, l] = Vm[M, NN]
                    NN += 1
            M += 1
    
        
    return full_tensor

                        
                