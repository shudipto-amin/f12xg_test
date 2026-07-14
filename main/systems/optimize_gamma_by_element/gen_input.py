import numpy as np
import argparse as ap

parser = ap.ArgumentParser()

parser.add_argument('-a', '--atom', type=str, help='Atom name', required=True)
parser.add_argument('-g', '--betas', nargs=3, metavar="<float>", type=float, required=True,
                    help='min max step - in that order, does not include max')
parser.add_argument('-o', '--outfile', type=str, help='output file for molpro to write table to')
parser.add_argument('-b', '--basis', type=str, default='aug-cc-pvtz')
parser.add_argument('-c', '--charge', type=int, default=0)

def arr_to_molpro_string(arr, width=4, prec=2):
    return "[" + ','.join(f'{num:{width}.{prec}f}' for num in arr) + "]"

def main(args):
    
    inp_template = """
geometry={{{atom}}}
set,charge={charge}
basis={basis}
gem_beta={beta_str}
{{df-hf}}
{{df-mp2;core,mixed}}
do i=1, #gem_beta
{{df-mp2-f12,gem_beta=[gem_beta(i)];core,mixed}}
e(i)=energy-energr
enddo
table,gem_beta,e;save,file='{outfile}'
    """

    
    inp_params = dict()
    inp_params['atom'] = args.atom
    inp_params['beta'] = np.arange(args.betas[0], args.betas[1], args.betas[2])
    inp_params['beta_str'] = arr_to_molpro_string(inp_params['beta'])
    inp_params['basis'] = args.basis
    inp_params['charge'] = args.charge
    if args.outfile is None:
        inp_params['outfile'] = "table_{atom}_{charge}_{basis}.csv".format(**inp_params)
    else:
        inp_params['outfile'] = args.outfile

    input_content = inp_template.format(**inp_params)
    print(input_content)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
