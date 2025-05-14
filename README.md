# RankEZ_CPM_Script
RankEZ_CPM_Script for credentials/discovery plugin

## AWS RediSSO Discovery CPM
Under development

## Doris Credential CPM
Prerequiste: Must install mysql-connector-python on remoteapp

![doris_credential_cpm](https://github.com/Julianchan-cyberforce/RankEZ_CPM_Script/blob/main/img/doris_credential_cpm.png?raw=true)

## Doris Discovery CPM
Under development

## Imperva Credential CPM
Under development 

## Imperva Discovery CPM
![imperva_discovery_cpm](https://github.com/Julianchan-cyberforce/RankEZ_CPM_Script/blob/main/img/imperva_discovery_cpm.png?raw=true)

Custom properties should be input as below:
```
{
	"x_api_id": "123456",
	"x_api_key": "11111111-2222-3333-4444-555566667777"
}
```

## RabbitMQ Credential CPM
![rabbitmq_credential_cpm](https://github.com/Julianchan-cyberforce/RankEZ_CPM_Script/blob/main/img/rabbitmq_credential_cpm.png?raw=true)

## RabbitMQ Discovery CPM
![rabbitmq_discovery_cpm](https://github.com/Julianchan-cyberforce/RankEZ_CPM_Script/blob/main/img/rabbitmq_discovery_cpm.png?raw=true)

## TenableIO Credential CPM
Under development

## TenableIO Discovery CPM
![tenableio_discovery_cpm](https://github.com/Julianchan-cyberforce/RankEZ_CPM_Script/blob/main/img/tenableio_discovery_cpm.png?raw=true)

Custom properties should be input as below:
```
{
	"x_apikeys": "accessKey=abcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcd; secretKey=abcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcd;"
}
```

Requires the Basic [16] user role. If the requesting user has the Administrator [64] user role, Tenable Vulnerability Management returns all attributes for individual user details. Otherwise, user details include only the uuid, id, username, and email attributes.
