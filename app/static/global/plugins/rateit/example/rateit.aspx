<%@ Page Language="C#" %>
<%
    //Get value
    float value = float.Parse(Request.Form["value"]);
    int productID = int.Parse(Request.Form["id"]);

    Response.Write(string.Format("You voted {0} on product: {1}.<br/>Time on server: {2}", value, productID, DateTime.Now.ToString()));

%>