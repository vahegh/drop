from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates/'))


async def generate_template(template_name: str, context: dict):
    template = env.get_template(template_name)
    body = template.render(context)
    return body
