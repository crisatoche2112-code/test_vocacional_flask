from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from io import BytesIO
from reportlab.pdfgen import canvas
import json
import os
import random  
from reportlab.lib.pagesizes import letter  # Para tamaño de página
from reportlab.lib.colors import blue, gray, black, lightblue  # Para colores
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont  # Para fuentes personalizadas (opcional)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "tu_clave_secreta_aqui")

# Configuración Base de Datos PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql://instance_qr0j_user:EhvbROiTvfugAiiPIxtHqTAsOfkywtYJ'
    '@dpg-d3td8mvdiees73deuf5g-a.oregon-postgres.render.com/instance_qr0j'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get("MAIL_USER", "testvocacional44@gmail.com"),
    MAIL_PASSWORD=os.environ.get("MAIL_PASS", "qzuwfvnfnybutjfm"), 
    MAIL_DEFAULT_SENDER=os.environ.get("MAIL_USER", "testvocacional44@gmail.com")
)

db = SQLAlchemy(app)
mail = Mail(app)

# Modelos de BD
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    edad = db.Column(db.Integer, nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)

class Resultado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False)
    perfil = db.Column(db.String(100), nullable=False)
    puntajes = db.Column(db.String(500), nullable=False) 


# Preguntas del test (tu lista completa)
preguntas = [
    {
        'texto': '¿Participarías como profesional en un espectáculo de acrobacia aérea?',
        'opciones': {
            'Sí': ['Realista'],
            'No': []
        }
    },
    {
        'texto': '¿Ante una situación de emergencia actúas rápidamente?',
        'opciones': {
            'Sí': ['Realista'],
            'No': []
        }
    }
]

# Carreras recomendadas por perfil (específicas y profesionales en Perú, ~60 total)
carreras_por_perfil = {
    "Realista": [
        "Ingeniería Civil",
        "Arquitectura",
        "Ingeniería de Minas",
        "Ingeniería Agrícola",
        "Ingeniería Pesquera",
        "Técnico en Construcción",
        "Técnico en Minería",
        "Operador de Maquinaria Pesada",
        "Bombero Profesional",
        "Guardaparques",
        "Ingeniería Ambiental",
        "Técnico en Electrónica Industrial",
        "Piloto de Aviación Civil",
        "Marino Mercante",
        "Soldado Profesional del Ejército"
    ],
    "Investigativo": [
        "Ingeniería de Sistemas",
        "Ingeniería de Redes y Telecomunicaciones",
        "Medicina",
        "Biología",
        "Química",
        "Física",
        "Estadística",
        "Economía",
        "Contabilidad",
        "Ingeniería Electrónica",
        "Ingeniería Mecánica",
        "Geología",
        "Investigación Científica",
        "Biotecnología",
        "Análisis de Datos"
    ],
    "Artístico": [
        "Arquitectura",
        "Diseño Gráfico",
        "Diseño de Moda",
        "Artes Plásticas",
        "Fotografía",
        "Música",
        "Teatro y Actuación",
        "Cine y Producción Audiovisual",
        "Turismo Cultural",
        "Guía de Turismo",
        "Diseño de Interiores",
        "Artesanías Tradicionales",
        "Escritura Creativa",
        "Publicidad y Marketing Digital",
        "Dirección de Arte"
    ],
    "Social": [
        "Psicología",
        "Educación Primaria",
        "Enfermería",
        "Trabajo Social",
        "Derechos Humanos",
        "Relaciones Internacionales",
        "Comunicación Social",
        "Administración Pública",
        "Desarrollo Comunitario",
        "Terapia Familiar",
        "Asistencia Social",
        "Periodismo",
        "Gestión de Recursos Humanos",
        "Educación Especial",
        "Salud Pública"
    ]
}


# Descripciones de perfiles (adaptadas a tu ejemplo)
descripciones_perfiles = {
    "Realista": {
        "titulo": "Realista",
        "caracteristicas": "Precisión Manual. Trabajo Práctico. Resistencia Física. Organización Técnica. Individuo Práctico.",
        "descripcion": "Intereses en actividades prácticas, al aire libre y con herramientas. Incluye profesiones en construcción, mecánica y agricultura."
    },
    "Investigativo": {
        "titulo": "Investigativo",
        "caracteristicas": "Precisión Intelectual. Investigación. Análisis. Curiosidad Científica. Individuo Analítico.",
        "descripcion": "Intereses en investigación, ciencia y resolución de problemas. Incluye profesiones en medicina, ingeniería y ciencias."
    },
    "Artístico": {
        "titulo": "Artístico",
        "caracteristicas": "Creatividad. Expresión Visual. Imaginación. Sensibilidad Estética. Individuo Innovador.",
        "descripcion": "Intereses en arte, diseño y expresión cultural. Incluye profesiones en artes plásticas, música y turismo."
    },
    "Social": {
        "titulo": "Social",
        "caracteristicas": "Empatía. Ayuda a Otros. Comunicación. Justicia. Individuo Solidario.",
        "descripcion": "Intereses en ayudar a personas, educación y relaciones sociales. Incluye profesiones en psicología, enfermería y trabajo social."
    }
}

# Función para generar PDF formal y decorado
def generar_pdf(perfil, puntajes, nombre_usuario, carreras):
    import random
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=20, textColor=blue, alignment=1, spaceAfter=20)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=16, textColor=blue, spaceAfter=10)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=12, spaceAfter=10)
    bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'], fontSize=12, leftIndent=20, spaceAfter=5)
    
    story = []
    
    # Título principal
    story.append(Paragraph("Reporte de Test Vocacional", title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Introducción
    intro_text = """
    Este reporte fue diseñado para ayudarte a elegir entre una extensa gama de opciones que te ofrece el campo educativo superior. 
    Una de las decisiones más importantes en la vida es la elección de carrera, así que el siguiente reporte se compone por los resultados 
    obtenidos del Test Vocacional que se han analizado para determinar las opciones que tienen una mayor posibilidad de proporcionar 
    resultados exitosos en tu desempeño profesional.
    """
    story.append(Paragraph(intro_text, normal_style))
    story.append(Spacer(1, 0.1 * inch))
    
    # Instrumento de evaluación
    story.append(Paragraph("INSTRUMENTO DE EVALUACIÓN:", heading_style))
    instrumento_text = """
    Test de Orientación Vocacional. Este test es una herramienta que se utiliza para evaluar y conocer tus intereses y habilidades 
    con referente a las actividades en el ámbito profesional en el que te gustaría desempeñarte. Identifica perfiles de intereses 
    y proporciona un panorama sobre algunas profesiones a elegir.
    """
    story.append(Paragraph(instrumento_text, normal_style))
    story.append(Spacer(1, 0.1 * inch))
    
    # Información del usuario
    story.append(Paragraph(f"Usuario: {nombre_usuario}", normal_style))
    story.append(Paragraph(f"Perfil predominante: {perfil}", normal_style))
    story.append(Spacer(1, 0.1 * inch))
    
    # Resultados obtenidos
    story.append(Paragraph("RESULTADOS OBTENIDOS:", heading_style))
    resultados_text = """
    Área de Intereses. Los intereses son las preferencias por realizar ciertas actividades. Es la inclinación y la motivación 
    que te hará realizar cierta actividad ocupacional, es decir, es la atracción que mantienes por un campo laboral. 
    A continuación se mencionan tus intereses obtenidos en la prueba:
    """
    story.append(Paragraph(resultados_text, normal_style))
    
    # Descripción del perfil
    perfil_data = descripciones_perfiles.get(perfil, {"titulo": perfil, "caracteristicas": "Características generales.", "descripcion": "Descripción no disponible."})
    story.append(Paragraph(f"• {perfil_data['titulo']}", bullet_style))
    story.append(Paragraph(f"Características: {perfil_data['caracteristicas']}", bullet_style))
    story.append(Paragraph(perfil_data['descripcion'], normal_style))
    story.append(Spacer(1, 0.1 * inch))
    
    # Puntajes en tabla
    story.append(Paragraph("Puntajes por perfil:", heading_style))
    data = [["Perfil", "Puntos"]] + [[k, str(v)] for k, v in puntajes.items()]
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), gray),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    story.append(table)
    story.append(Spacer(1, 0.2 * inch))
    
    # Carreras recomendadas
    if carreras and len(carreras) > 0:
        carreras_sugeridas = random.sample(carreras, min(10, len(carreras)))
        story.append(Paragraph("Carreras Recomendadas:", heading_style))
        for i, carrera in enumerate(carreras_sugeridas, 1):
            story.append(Paragraph(f"{i}. {carrera}", bullet_style))
    
    # Pie de página
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Generado por Test Vocacional - Fecha: " + str(__import__('datetime').datetime.now().date()), ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, textColor=gray, alignment=1)))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


# Rutas principales
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        apellido = request.form['apellido'].strip()
        edad = request.form.get('edad', type=int)
        correo = request.form['correo'].strip().lower()
        if not (14 <= edad <= 19):
            flash('La edad debe estar entre 14 y 19 años.', 'error')
            return render_template('registro.html')
        if Usuario.query.filter_by(correo=correo).first():
            flash('El correo ya está registrado.', 'error')
            return render_template('registro.html')
        nuevo_usuario = Usuario(nombre=nombre, apellido=apellido, edad=edad, correo=correo)
        db.session.add(nuevo_usuario)
        db.session.commit()
        session['usuario_id'] = nuevo_usuario.id
        session['nombre_usuario'] = nombre
        flash('Registro exitoso. Ahora responde el test.', 'success')
        return redirect(url_for('test'))
    return render_template('registro.html')
@app.route('/test', methods=['GET', 'POST'])
def test():
    if 'usuario_id' not in session:
        flash('Debes registrarte primero.', 'error')
        return redirect(url_for('registro'))
    if request.method == 'POST':
        respuestas = [request.form.get(f'respuesta{i}') for i in range(len(preguntas))]
        if any(r is None or (isinstance(r, str) and r.strip() == "") for r in respuestas):
            flash('Debes responder todas las preguntas.', 'error')
            return render_template('test.html', preguntas=preguntas, nombre=session.get('nombre_usuario'))
        session['respuestas'] = respuestas
        puntajes = {}
        for i, respuesta in enumerate(respuestas):
            perfiles = preguntas[i]['opciones'].get(respuesta, [])
            for perfil in perfiles:
                puntajes[perfil] = puntajes.get(perfil, 0) + 1
        perfil_predominante = max(puntajes, key=puntajes.get) if puntajes else 'No definido'
        # Obtener carreras recomendadas
        carreras_recomendadas = carreras_por_perfil.get(perfil_predominante, [])
        session['carreras'] = carreras_recomendadas
        resultado = Resultado(
            usuario_id=session['usuario_id'],
            perfil=perfil_predominante,
            puntajes=json.dumps(puntajes)
        )
        db.session.add(resultado)
        db.session.commit()
        session['perfil'] = perfil_predominante
        session['puntajes'] = puntajes
        # Generar PDF con carreras
        usuario = Usuario.query.get(session['usuario_id'])
        # pdf_buffer = generar_pdf(perfil_predominante, puntajes, usuario.nombre, carreras_recomendadas)
        try:
            msg = Message("Resultados Test Vocacional", recipients=[usuario.correo])
            msg.body = f"Hola {usuario.nombre},\n\nAdjunto encontrarás tu reporte del test vocacional.\n\nSaludos."
            # msg.attach("resultado_test.pdf", "application/pdf", pdf_buffer.read())
            # mail.send(msg)
            flash('Reporte PDF enviado a tu correo.', 'success')
        except Exception as e:
            flash(f'Error al enviar correo: {str(e)}', 'error')
        return redirect(url_for('resultados'))
    return render_template('test.html', preguntas=preguntas, nombre=session.get('nombre_usuario'))
@app.route('/resultados')
def resultados():
    respuestas = session.get('respuestas', [])
    perfil = session.get('perfil', 'No definido')
    puntajes = session.get('puntajes', {})
    carreras = session.get('carreras', [])
    if not respuestas:
        flash('No hay respuestas para mostrar. Por favor realiza el test primero.', 'error')
        return redirect(url_for('test'))
    return render_template('resultados.html', respuestas=respuestas, perfil=perfil, puntajes=puntajes, carreras=carreras)
# Iniciar la app
if __name__ == '__main__':
    app.run(debug=True)
