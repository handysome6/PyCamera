import requests
import datetime


def upload(imageName,imgL,imgR,model):
    '''

    Parameters
    ----------
    imageName : str, should be a unique name
    imgL: str, should be a unique name
    imgR : str, should be a unique name
    model : str, if the content of the model changed, the model name should change accordingly

    Returns
    -------

    '''
    url = "http://localhost:8082/model/uploadimagesdata" #http://192.168.10.194:8082
    form_data = {}
    today = datetime.date.today()
    form_data["imagename"] = imageName
    form_data["left"] = "/home/hyx/Desktop/codeshere/PyCamera/resources/"+imgL
    form_data["right"] = "/home/hyx/Desktop/codeshere/PyCamera/resources/"+imgR
    form_data["model"] = "/home/hyx/Desktop/codeshere/PyCamera/resources/"+model
    form_data["date"] = today
    form_data["preview"] = "/home/hyx/Desktop/codeshere/PyCamera/resources/"+imgL

    response=requests.post(url,data=form_data)
    print(response.text)


if __name__ == "__main__":
    upload("testimage2", "left.jpg", "right.jpg", "model.json")


