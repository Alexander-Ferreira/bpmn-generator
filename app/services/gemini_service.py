import os
import re
import google.generativeai as genai
from flask import current_app
from dotenv import load_dotenv
from lxml import etree

# Configuración inicial
load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))


def generate_bpmn(description):
    """Genera XML BPMN con validación de entrada"""
    try:
        # Validar que la descripción no esté vacía
        if not description or not isinstance(description, str) or not description.strip():
            raise ValueError("La descripción del proceso no puede estar vacía")
        
        # Generar el prompt
        prompt = create_bpmn_prompt(description)
        
        # Validar que el prompt no esté vacío
        if not prompt or not prompt.strip():
            raise ValueError("El prompt generado está vacío")
        
        # Configurar el modelo va variando la version 
        model = genai.GenerativeModel('gemini-1.5-pro-latest') 
        
        # Crear contenido estructurado para la API
        contents = {
            "parts": [{
                "text": prompt
            }]
        }
        
        # Llamar a la API
        response = model.generate_content(
            contents=contents,  
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 4000
            }
        )
        
        # Verificar que haya respuesta
        if not response or not response.text:
            raise ValueError("La API no devolvió contenido")
        
        # Procesar la respuesta
        current_app.logger.debug(f"Respuesta cruda de Gemini:\n{response.text[:500]}...")  # Log parcial
        
        bpmn_xml = extract_bpmn_xml(response.text)
        validate_bpmn_structure(bpmn_xml)
        
        return bpmn_xml
        
    except Exception as e:
        current_app.logger.error(f"Error en generate_bpmn. XML generado:\n{xml_content[:1000]}...")
        raise RuntimeError(f"Error al generar BPMN: {str(e)}")


#Creo el prompt para el bpmn
def create_bpmn_prompt(description):
    """Prompt optimizado para incluir todos los namespaces requeridos"""
    return f"""
    GENERA UN DOCUMENTO XML BPMN 2.0 COMPLETO Y VÁLIDO para:
    "{description}"

    REQUISITOS ESTRICTOS:
    1. Debe incluir TODOS los namespaces necesarios:
       - xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
       - xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
       - xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
       - xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
    2. Estructura completa con:
       - Declaración XML
       - Elemento raíz bpmn:definitions
       - bpmn:process con elementos del flujo
       - bpmndi:BPMNDiagram con la diagramación
    3. Ejemplo completo:
    <?xml version="1.0"?>
    <bpmn:definitions 
      xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
      xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
      xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
      xmlns:di="http://www.omg.org/spec/DD/20100524/DI">
      <!-- Contenido del proceso -->
    </bpmn:definitions>
    """

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

