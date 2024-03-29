#!/usr/bin/python3

import yaml, json # for loading the parameters file in yaml/json format
from dataclasses import dataclass, asdict
from collections import namedtuple
from utils import CICError


# 
# options table for count-in-cells calculation
#
@dataclass(slots = True, kw_only = True)
class Options:
    random_catalog_path            : str   = None
    random_catalog_compression     : str   = None
    random_catalog_chunk_size      : int   = None
    random_catalog_delimiter       : str   = None
    random_catalog_comment         : str   = None
    random_catalog_header          : int   = None
    random_catalog_colnames        : list  = None
    random_catalog_mask            : str   = None
    random_catalog_x_coord         : str   = None
    random_catalog_y_coord         : str   = None
    random_catalog_filters         : list  = None
    random_catalog_expressions     : list  = None
    object_catalog_path            : str   = None
    object_catalog_compression     : str   = None
    object_catalog_chunk_size      : int   = None
    object_catalog_delimiter       : str   = None
    object_catalog_comment         : str   = None
    object_catalog_header          : int   = None
    object_catalog_colnames        : list  = None
    object_catalog_redshift        : str   = None
    object_catalog_redshift_error  : str   = None
    object_catalog_magnitude       : str   = None
    object_catalog_magnitude_offset: str   = None
    object_catalog_mask            : str   = None
    object_catalog_x_coord         : str   = None
    object_catalog_y_coord         : str   = None
    object_catalog_filters         : list  = None
    object_catalog_expressions     : list  = None
    counting_region_rect           : list  = None
    counting_patchsize_x           : float = None
    counting_patchsize_y           : float = None
    counting_remove_regions        : list  = None
    counting_cellsize              : float = None
    counting_random_mask           : list  = None
    counting_object_mask           : list  = None
    counting_max_subdiv            : int   = None
    distribution_masked_frac       : float = None
    distribution_max_count         : int   = None # 
    distribution_count_files       : list  = None # path(s) files storing the count data   
    distribution_patch_files       : list  = None # path(s) files storing the patch data   
    output_dir                     : str   = None # directory to write / look for output files
    all_bands                      : list  = None
    
    def _save_as(self, file: str):
        r"""
        Write the options into a text file.
        """

        with open( file, 'w' ) as fp:
            for __key, __value in asdict( self ).items():
                if __value is None:
                    continue
                fp.write( f"{__key:32s}: " )
                if isinstance(__value, list):
                    if len(__value) == 0:
                        fp.write( "[]\n" )
                        continue
                    
                    __value = list(map(str, __value))
                    m       = max( map(len, __value) )
                    if m * len(__value) < 32:
                        fp.write( "[" + ", ".join(__value) + "]\n" )
                    else:
                        __value = ',\n\t\t'.join( __value )
                        fp.write( "[\n\t\t" + __value + "\n\t]\n"  )
                else:
                    fp.write( f"{__value}\n" )
        return 
        

_OptionBlock = namedtuple( '_OptionBlock', ['name', 'fields'] )


def __load_options(file: str):

    if file is None:
        return {}

    # try yaml format first
    try:
        with open(file, 'r') as fp:
            return yaml.safe_load( fp )
    except Exception:
        pass

    # try json format then
    try:
        with open(file, 'r') as fp:
            return json.load( fp )
    except Exception:
        pass

    # raise error: not a valid json or yaml
    raise CICError(f"cannot load options from '{file}', must be a valid JSON or YAML file")


# structure of the options
opt_tree = (
            _OptionBlock( 
                            name   = 'random_catalog',
                            fields = [
                                        'path',
                                        'compression',
                                        'chunk_size', 
                                        'delimiter',
                                        'comment',
                                        'header',
                                        'colnames',              
                                        'mask',    
                                        'x_coord',
                                        'y_coord',                 
                                        'filters', 
                                        'expressions', 
                                    ] 
                        ),
            _OptionBlock( 
                            name   = 'object_catalog',
                            fields = [
                                        'path',
                                        'compression',
                                        'chunk_size',
                                        'delimiter',
                                        'comment',
                                        'header',
                                        'colnames',               
                                        'redshift',                    
                                        'redshift_error',              
                                        'magnitude',                
                                        'magnitude_offset',          
                                        'mask',    
                                        'x_coord',
                                        'y_coord',                 
                                        'filters', 
                                        'expressions', 
                                    ] 
                        ),
            _OptionBlock( 
                            name = 'counting',
                            fields = [
                                        'cellsize',
                                        'max_subdiv',
                                        'region_rect',
                                        'patchsize_x',
                                        'patchsize_y',
                                        'random_mask',
                                        'object_mask',
                                        'remove_regions',
                                     ]
                        ),
            _OptionBlock(
                            name = 'distribution',
                            fields = [
                                        'masked_frac',                
                                        'max_count',
                                        'count_files',
                                        'patch_files',
                                     ]
                        ),
            'output_dir',
            'all_bands',
            )

def load_options(file: str, alt_file: str = None) -> Options:
    r"""
    Load count-in-cells measurements options from a YAML/JSON file.
    """

    def __get_field(key: str, tree: dict, alt_tree: dict = None):
        
        if alt_tree is None:
            alt_tree = {}

        value = tree.get(key)
        if value is None:
            value = alt_tree.get(key)

        return value

    # load files
    _opts     = __load_options( file )
    _alt_opts = __load_options( alt_file )

    options = Options()
    for item in opt_tree:

        if not isinstance(item, _OptionBlock): # i.e, item is a field (str)

            value = __get_field( item, _opts, _alt_opts )
            setattr( options, item, value )

        else: # item is a block of fields

            block, alt_block = _opts.get( item.name ), _alt_opts.get( item.name )
            if block is None:
                block = {}
            if alt_block is None:
                alt_block = {}

            for field in item.fields:
                
                value = __get_field( field, block, alt_block )
                setattr( options, '_'.join([ item.name, field ]), value )
    
    return options

