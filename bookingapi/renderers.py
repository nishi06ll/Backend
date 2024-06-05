from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.http import HttpResponse

def render_to_pdf(template_src, context_dict={}):
    # Render the template with the given context
    template = get_template(template_src)
    html = template.render(context_dict)

    # Create a BytesIO buffer to receive the PDF data
    result = BytesIO()

    # Generate the PDF
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)

    # Check for errors during PDF generation
    if pdf.err:
        return HttpResponse("Invalid PDF", status=400, content_type='text/plain')

    # Return the PDF content as an HttpResponse
    return HttpResponse(result.getvalue(), content_type='application/pdf')
