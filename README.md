# DevSecOps – Pruebas automatizadas de seguridad

Proyecto de la asignatura **OCY1102 Ciberseguridad en desarrollo** (Duoc UC), guías 3.2.2 y 3.2.3.

Aplicación Flask **intencionalmente vulnerable** (XSS reflejado y modo debug activo) usada para
demostrar un pipeline CI/CD en Jenkins con SonarQube, OWASP Dependency-Check y OWASP ZAP.

> ⚠️ No desplegar en producción.

## Ejecutar localmente

```bash
pip install -r requirements.txt
python app.py
# http://localhost:5000/hello?name=TEST
```
