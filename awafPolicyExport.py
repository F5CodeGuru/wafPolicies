#This script requires python 3
#To run 
#python3 <scriptname>.py --policy <asm policy name>
#This script takes an asm policy name as an argument and will export it as xml
#The script then fetches a policy from github and creates a new virtual w/ the asm policy from github applied

import requests, re, argparse
import json, sys, time
requests.packages.urllib3.disable_warnings() 
import datetime
 

#Globals, 
#Configurable globals, should be configured to match your environment
adminUser = 'admin'
adminPass = 'bigip123'
host = 'https://10.3.111.10'
#End configurable globals

asmPoliciesPath = '/mgmt/tm/asm/policies/'
#Auth token header name
f5AuthHeaderName = 'X-F5-Auth-Token'
f5RestApiAuthPath = '/mgmt/shared/authn/login'
asmSignaturesPath = '/mgmt/tm/asm/signatures?options=non-default-properties'
disableSigStagingJson = '{"performStaging":"false"}'
applyPolicyUrl = host  + '/mgmt/tm/asm/tasks/apply-policy'
policyId = ''
f5AuthToken = ''
#Create auth token so that we only login once
authDataJson = '{"username":"' + adminUser + '", "password":"' + adminPass + '","loginProviderName": "tmos"}'
wafRestApiExportPolicyUrl = host  + '/mgmt/tm/asm/tasks/export-policy'
wafExportedPolicyUrl = host + '/mgmt/tm/asm/file-transfer/downloads/'

#Declarative url
as3DeclareUrl = host + '/mgmt/shared/appsvcs/declare'

#Content type needed to tell rest server what type of content is being sent
restHeaders = {

    'Content-Type': 'application/json; charset=UTF-8'

}

#Url to all policies
asmPoliciesUrl = host + asmPoliciesPath
asmRestApiAuthUrl = host + f5RestApiAuthPath
#Global to save the actual url of the asm policy
asmPolicyIdUrl = ''
#If the policy specified as the argument is found
asmPolicyFoundStatus = 0

#Require Python v3 or greater
if sys.version_info[:3] < (3,0,0):
    print('requires Python >= 3.0.0')
    sys.exit(1)


#command line args, only require policy name (so that we can get the ID)
parser = argparse.ArgumentParser()
parser.add_argument('--policy',required=True)
args = parser.parse_args()
wafPolicyName = args.policy


#funciton to get auth token so each request does not need to go through authentication process
def getRestApiAuthToken():

	authResponse = requests.post(url=asmRestApiAuthUrl,headers=restHeaders,data=authDataJson,verify=False)
	authResponseJson = json.loads(authResponse.text)
	restHeaders[f5AuthHeaderName] = authResponseJson['token']['token']

#Get the asm policy id from the name
def wafReturnPolicyIdFromName(wafPolicyName):

	asmPoliciesData = requests.get(url=asmPoliciesUrl,headers=restHeaders,verify=False)

	#Load json output into a python dictionary format
	asmPoliciesDataJson = json.loads(asmPoliciesData.text)

	#Loop through each policy to find which one equals the command line argument
	for policy in asmPoliciesDataJson['items']:
	
		#Check to find the policy 
		if (policy['name'] == wafPolicyName):
		
			#If found
			policyId = policy['id'] 
		
			return policyId

#Export policy as xml
def wafExportPolicy(policyID):

	# Get current date and time
	dt = datetime.datetime.now()
 
	# Format datetime string
	dateString = dt.strftime("%Y-%m-%d-%H-%M-%S")


	policyExportJsonDict = {}
	policyRefDict = {}
	
	#Give exported filename a unique name by appending a timestamp to guarantee uniqueness
	wafExportPolicyFilename = wafPolicyName + '-' + dateString

	
	policyExportJsonDict['filename'] = wafExportPolicyFilename
	policyRefDict['link'] = 'https://localhost/mgmt/tm/asm/policies/' + policyID
	
	policyExportJsonDict['policyReference'] = policyRefDict
	

	
	#Export policy
	#Policy will be saved in /var/ts/rest 
	authResponse = requests.post(url=wafRestApiExportPolicyUrl,headers=restHeaders,data=json.dumps(policyExportJsonDict),verify=False)
	
	
	print("Export filename: " + wafExportedPolicyUrl + wafExportPolicyFilename)
	time.sleep(2.0)
	fileResp = requests.get(url=wafExportedPolicyUrl + wafExportPolicyFilename,headers=restHeaders,verify=False)

	
	open(wafExportPolicyFilename, 'wb').write(fileResp.content)

#Use as3 to declare a new configuration
def sendAS3Declaration():

	with open('wafPolicy.as3','rb') as payload:

		fileUploadResponse = requests.post(url=as3DeclareUrl,data=payload,headers=restHeaders,verify=False)
		
		
getRestApiAuthToken()	
policyID = wafReturnPolicyIdFromName(wafPolicyName)
	
print("Waf Policy ID: " + policyID )	
wafExportPolicy(policyID)
sendAS3Declaration()








