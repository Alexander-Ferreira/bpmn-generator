import re
from lxml import etree
from flask import current_app

#Extragio el bpmn del xml 
def extract_bpmn_xml(full_response):
    """Extracción robusta que maneja diferentes formatos de respuesta"""
    try:
        # Intento 1: Buscar XML completo
        xml_match = re.search(
            r'(<\?xml\b[^>]*>\s*<bpmn:definitions[\s\S]*?<\/bpmn:definitions>)',
            full_response,
            re.IGNORECASE
        )
        if xml_match:
            return xml_match.group(1).strip()

        # Intento 2: Buscar sin declaración XML
        definitions_match = re.search(
            r'(<bpmn:definitions[\s\S]*?<\/bpmn:definitions>)',
            full_response,
            re.IGNORECASE
        )
        if definitions_match:
            return f'<?xml version="1.0"?>\n{definitions_match.group(1).strip()}'

        # Intento 3: Buscar fragmentos BPMN
        if '<bpmn:' in full_response:
            start = full_response.find('<bpmn:')
            end = full_response.rfind('</bpmn:definitions>') + len('</bpmn:definitions>')
            if start != -1 and end != -1:
                potential_xml = full_response[start:end]
                if '<bpmn:definitions' in potential_xml:
                    return f'<?xml version="1.0"?>\n{potential_xml.strip()}'

        raise ValueError("No se pudo extraer XML BPMN válido de la respuesta")
        
    except Exception as e:
        current_app.logger.error(f"Error en extraer el xml: {str(e)}")
        current_app.logger.debug(f"Respuesta problemática:\n{full_response[:1000]}...")
        raise

#Valido la estructura de los BPMN
def validate_bpmn_structure(xml_content):
    """Validación mejorada del XML BPMN con manejo correcto de namespaces"""
    try:
        # Verificar que el XML no esté vacío
        if not xml_content or not xml_content.strip():
            raise ValueError("El contenido XML está vacío")

        # Añadir declaración XML si falta
        if not xml_content.lstrip().startswith('<?xml'):
            xml_content = f'<?xml version="1.0"?>\n{xml_content}'

        # Configurar parser
        parser = etree.XMLParser(resolve_entities=False)
        tree = etree.fromstring(xml_content.encode('utf-8'), parser)

        # Namespaces necesarios para BPMN
        ns = {
            'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
            'dc': 'http://www.omg.org/spec/DD/20100524/DC',
            'di': 'http://www.omg.org/spec/DD/20100524/DI'
        }

        # Validar elementos esenciales con namespaces
        required_elements = [
            ('bpmn:process', 'Debe contener un elemento bpmn:process'),
            ('bpmn:startEvent', 'Debe tener al menos un startEvent'),
            ('bpmn:endEvent', 'Debe tener al menos un endEvent'),
            ('bpmndi:BPMNDiagram', 'Debe incluir un diagrama BPMN')
        ]

        for elem, error_msg in required_elements:
            if not tree.xpath(f'//{elem}', namespaces=ns):
                raise ValueError(error_msg)

        return True

    except etree.XMLSyntaxError as e:
        raise ValueError(f"Error de sintaxis XML: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error validando estructura BPMN: {str(e)}")



# def clean_bpmn_xml(xml_content):
#     """
#     Extrae el XML BPMN de la respuesta de Gemini, eliminando todo el texto adicional.
#     """
#     try:
#         # Patrón para encontrar el XML completo (desde <?xml hasta </bpmn:definitions>)
#         xml_pattern = r'(<\?xml[\s\S]+<\/bpmn:definitions>)'
#         match = re.search(xml_pattern, xml_content)
        
#         if not match:
#             current_app.logger.error("No se encontró XML BPMN en la respuesta")
#             raise ValueError("La respuesta no contiene un XML BPMN válido")
            
#         clean_xml = match.group(1)
        
#         # Eliminar espacios múltiples y normalizar saltos de línea
#         clean_xml = re.sub(r'\s+', ' ', clean_xml)
#         clean_xml = re.sub(r'>\s+<', '><', clean_xml)
        
#         return clean_xml.strip()
        
#     except Exception as e:
#         current_app.logger.error(f"Error limpiando XML: {str(e)}")
#         raise ValueError(f"Error procesando el XML: {str(e)}")

