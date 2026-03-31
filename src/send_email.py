import smtplib
import os
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from src.config import settings
from datetime import datetime

def dataframe_a_html(df):
    """
    Convierte un DataFrame de Pandas a una tabla HTML con estilos básicos.
    """
    if df is None or df.empty:
        return "<p>No hay datos disponibles para este reporte.</p>"
    
    # Renderizar el HTML de Pandas
    html = df.to_html(index=False, border=1, classes='report-table')
    
    # Limpiar y agregar estilos inline simples
    html = html.replace('<table border="1" class="dataframe report-table">', '<table border="1" style="border-collapse: collapse; margin-top: 10px; font-size: 14px; width: 100%;">')
    html = html.replace('<th>', '<th style="padding: 8px; text-align: center; background-color: #f2f2f2; border: 1px solid #ddd;">')
    html = html.replace('<td>', '<td style="padding: 8px; text-align: left; border: 1px solid #ddd;">')
    
    return html

def enviar_correo_reporte(titulo_reporte, df=None, mensaje_extra="", adjuntos=[], destinatarios=[]):
    """
    Envía un correo estandarizado con un DataFrame integrado como HTML.
    """
    if not destinatarios:
             print(">> No hay destinatarios configurados. Saltando envío de correo.")
             return
             
    smtp_server = settings.SMTP_SERVER 
    smtp_port = settings.SMTP_PORT 
    smtp_username = settings.SMTP_USERNAME 
    smtp_password = settings.SMTP_PASSWORD 
    from_email = settings.SMTP_USERNAME if settings.SMTP_USERNAME else 'bicorp@castano.cl'
    
    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Si viene un DF, preparamos la tabla
    tabla_html = dataframe_a_html(df) if isinstance(df, pd.DataFrame) else ""
    
    # Asunto con estado (si DataFrame viene vacío o no)
    hay_datos = (df is not None and not df.empty) or ("<table" in mensaje_extra.lower())
    estado = "✅" if hay_datos else "⚠️ VACIO"
    subject = f'{estado} {titulo_reporte} - {fecha_hoy}'
    
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = ', '.join(destinatarios)
    msg['Subject'] = subject

    # Cuerpo del mensaje
    body = f'''
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #3d2314;">{titulo_reporte}</h2>
        <p>Fecha de generación: <strong>{fecha_hoy}</strong></p>
        <p>{mensaje_extra}</p>
        <br>
        {tabla_html}
        <br>
        <p style="font-size: 12px; color: #777; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
            Este es un reporte automático generado por Reportería Prefect.<br>Por favor no responder.
        </p>
    </body>
    </html>
    '''
    msg.attach(MIMEText(body, 'html'))

    # Adjuntos
    for ruta_archivo in adjuntos:
        if os.path.exists(ruta_archivo):
            try:
                with open(ruta_archivo, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(ruta_archivo)}",
                )
                msg.attach(part)
            except Exception as e:
                 print(f"No se pudo adjuntar {ruta_archivo}: {e}")

    # Envío
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, destinatarios, msg.as_string())
        print(f'>> Correo "{titulo_reporte}" enviado exitosamente a {len(destinatarios)} destinatarios.')
    except Exception as e:
        print(f"** Error al enviar correo: {e}")
