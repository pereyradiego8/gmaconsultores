/* GMA preview: client-side mail composition. No user data leaves this
   browser until the visitor personally sends the email in their mail client. */
(() => {
  "use strict";
  const selectors={contact:"#gma-contact-form",apply:"#gma-application-form",newsletter:"#gma-newsletter-form"};
  const q=(root,name)=>root.elements.namedItem(name)?.value?.trim()||"";
  const safe=(str,max)=>String(str||"").replace(/[\r\n\x00-\x1f]/g," ").slice(0,max).trim();
  const text=(str,max=2000)=>String(str||"").replace(/\r/g,"").slice(0,max).trim();
  function compose({form,to,subject,body}){
    if (!form.reportValidity()) return;
    const status=form.querySelector('[role="status"]');
    const url="mailto:"+to+"?subject="+encodeURIComponent(safe(subject,145))+"&body="+encodeURIComponent(text(body,2800));
    if(status){
      status.textContent="Se preparó el correo. Revisá el mensaje en tu aplicación de email y presioná Enviar. Si no se abre, usá el enlace al formulario oficial.";
    }
    window.location.href=url;
  }
  const contact=document.querySelector(selectors.contact);
  if(contact){
    contact.addEventListener("submit",event=>{
      event.preventDefault();
      const nombre=safe(q(contact,"nombre"),120),email=safe(q(contact,"email"),180),
        empresa=safe(q(contact,"empresa"),120),servicio=safe(q(contact,"servicio"),90),
        mensaje=text(q(contact,"mensaje"));
      compose({form:contact,to:"info@gmaconsultores.com.ar",
        subject:"Consulta web GMA - "+(servicio||"General"),
        body:"Nombre: "+nombre+"\nCorreo: "+email+
          "\nEmpresa: "+(empresa||"No indicada")+"\nServicio: "+(servicio||"General")+
          "\n\nMensaje:\n"+mensaje+"\n\nEnviado voluntariamente desde la versión renovada de GMA."});
    });
  }
  const apply=document.querySelector(selectors.apply);
  if(apply){
    const select=apply.elements.namedItem("puesto");
    const search=new URLSearchParams(location.search).get("puesto");
    if(search && select){
      for(const option of select.options){
        if(option.value===search){select.value=search;break;}
      }
    }
    apply.addEventListener("submit",event=>{
      event.preventDefault();
      const puesto=safe(q(apply,"puesto"),150),nombre=safe(q(apply,"nombre"),130),
        correo=safe(q(apply,"email"),180),telefono=safe(q(apply,"telefono"),80),
        mensaje=text(q(apply,"mensaje"),1200);
      compose({form:apply,to:"rrhh@gmaconsultores.com.ar",
        subject:"Postulación GMA - "+puesto,
        body:"Postulación para: "+puesto+"\nNombre: "+nombre+"\nEmail: "+correo+
        "\nTeléfono: "+(telefono||"No indicado")+
        "\n\nPresentación:\n"+mensaje+
        "\n\nIMPORTANTE: adjuntar CV y, si el aviso lo solicita, remuneración pretendida antes de enviar."});
    });
  }
  const newsletter=document.querySelector(selectors.newsletter);
  if(newsletter){
    newsletter.addEventListener("submit",event=>{
      event.preventDefault();
      const email=safe(q(newsletter,"email"),180);
      compose({form:newsletter,to:"info@gmaconsultores.com.ar",
        subject:"Solicitud de suscripción al newsletter GMA",
        body:"Hola, solicito información para suscribirme a las novedades de GMA.\nEmail: "+email+
          "\n\nEntiendo que este mensaje es una solicitud y que la suscripción no es automática."});
    });
  }
})();