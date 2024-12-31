"""
This program takes a series of csv files, interpreted through
info dictionaties, and outputs a series of SVG map files to
show GDP by country for a given year. 
"""

import csv
import math
import pygal

def build_country_code_converter(codeinfo):
    """
    Inputs:
      codeinfo      - A country code information dictionary

    Output:
      A dictionary whose keys are plot country codes and values
      are world bank country codes, where the code fields in the
      code file are specified in codeinfo.
    """
    # dictionary to be populated / passed
    converter = {}
    
    # open file based on info dictionary
    with open(codeinfo['codefile'], newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=codeinfo['separator'],
                                quotechar=codeinfo['quote'])
    # iterate over entries in reader
        for row in reader:
            plot_code = row[codeinfo['plot_codes']]
            data_code = row[codeinfo['data_codes']]
            converter[plot_code] = data_code
    # return populated dictionary
    return converter


def reconcile_countries_by_code(codeinfo, plot_countries, gdp_countries):
    """
    Inputs:
      codeinfo       - A country code information dictionary
      plot_countries - Dictionary whose keys are plot library country codes
                       and values are the corresponding country name
      gdp_countries  - Dictionary whose keys are country codes used in GDP data

    Output:
      A tuple containing a dictionary and a set. The dictionary maps
      country codes from plot_countries to country codes from
      gdp_countries.  The set contains the country codes from
      plot_countries that did not have a country with a corresponding
      code in gdp_countries.

      Note that all codes should be compared in a case-insensitive
      way.  However, the returned dictionary and set should include
      the codes with the exact same case as they have in
      plot_countries and gdp_countries.
    """
    # use previous function to establish necessary dictionary
    codeinfo2 = build_country_code_converter(codeinfo)
    
    # assign the output dictionary / set
    output_dict = {}
    missing_from_gdp = set()
    
    #assign casefolded dictionaries to match keys
    cf_plot = {}
    cf_gdp = {}
    cf_codeinfo = {}
    
    #create an intermediary dictionary to pass values    
    inter_dict = {}


    # Created casefolded input dictionaries for easy comparison
    for key in plot_countries:
        cf_plot[key.casefold()] = key
    
    for key in gdp_countries:
        cf_gdp[key.casefold()] = key

    for keys, values in codeinfo2.items():
        cf_codeinfo[keys.casefold()] = values.casefold()
        
    #compare keys to create intermediary dictionary
    for keys1, values1 in cf_codeinfo.items():
        if keys == keys1:
            if keys in cf_codeinfo:
                inter_dict[values] = values1

    # compare intermediary to gdp for output dictionary
    for keys, values in inter_dict.items():
        for keys1, values1 in cf_gdp.items():
            if values == keys1:
                output_dict[keys] = values1
    # for values not in gdp dict, pass to missing_from_gdp
    for keys, values in inter_dict.items():
        if values not in cf_gdp:
            missing_from_gdp.add(keys)
    
    return output_dict, missing_from_gdp 


def build_map_dict_by_code(gdpinfo, codeinfo, plot_countries, year):
    """
    Inputs:
      gdpinfo        - A GDP information dictionary
      codeinfo       - A country code information dictionary
      plot_countries - Dictionary mapping plot library country codes to country names
      year           - String year for which to create GDP mapping

    Output:
      A tuple containing a dictionary and two sets.  The dictionary
      maps country codes from plot_countries to the log (base 10) of
      the GDP value for that country in the specified year.  The first
      set contains the country codes from plot_countries that were not
      found in the GDP data file.  The second set contains the country
      codes from plot_countries that were found in the GDP data file, but
      have no GDP data for the specified year.
    """
    #assign output dicts
    gdp_data = {}
    missing_gdp = set()
    missing_year = set()

    # Read the GDP data for the specified year from csv file
    with open(gdpinfo['gdpfile'], newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=gdpinfo['separator'], quotechar=gdpinfo['quote'])
        
        # iterate over rows from reader
        for row in reader:
            country_code = row[gdpinfo['country_code']].upper()
            gdp_value = row[year]
            
            # assign gdp or country to appropriate output, based on whether found
            if gdp_value:
                gdp_data[country_code] = float(gdp_value)
            else:
                missing_year.add(country_code)
                
    #assign output dict
    map_dict = {}
    for plot_code in plot_countries:
        # Get the corresponding data country code
        plot_code_lower = plot_code.lower()
        
        if plot_code_lower in codeinfo:
            data_code = codeinfo[plot_code_lower]
            
            if data_code in gdp_data:
                # Logarithmic scaling for GDP, to increase color contrast
                map_dict[plot_code] = math.log10(gdp_data[data_code])
            else:
                missing_gdp.add(plot_code)
    
    return map_dict, missing_gdp, missing_year

def render_world_map(gdpinfo, codeinfo, plot_countries, year, map_file):
    """
    Inputs:
      gdpinfo        - A GDP information dictionary
      codeinfo       - A country code information dictionary
      plot_countries - Dictionary mapping plot library country codes to country names
      year           - String year of data
      map_file       - String that is the output map file name

    Output:
      Returns None.

    Action:
      Creates a world map plot of the GDP data in gdp_mapping and outputs
      it to a file named by svg_filename.
    """
    # Create the map dictionary and get the missing data
    map_dict, missing_gdp, missing_year = build_map_dict_by_code(gdpinfo,
                                                                 codeinfo, plot_countries, year)
    
    # Create the world map plot
    worldmap = pygal.maps.world.World()
    
    # Set the title and legend
    worldmap.title = f"GDP by Country for {year} (Logarithmic Scale)"
    worldmap.add('GDP Data Available', map_dict)
    
    # Add countries with missing data
    worldmap.add('Missing GDP Data', list(missing_gdp))
    worldmap.add('Missing Year Data', list(missing_year))
    
    # Render the map to an SVG file
    worldmap.render_to_file(map_file)


