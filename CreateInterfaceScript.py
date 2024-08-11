from extras.scripts import Script, ChoiceVar, ObjectVar, StringVar, IntegerVar
from dcim.models import Device, Interface, Site
from ipam.models import IPAddress, VLAN
from django.contrib.contenttypes.models import ContentType

class CreateInterfaceScript(Script):
    class Meta:
        name = "Create Interface for Solution"
        description = "Creates an interface on the device and POP based on the chosen solution"

    device = ObjectVar(
        description="Select the device",
        model=Device,
        required=True
    )

    pop_device = ObjectVar(
        description="Select the POP device",
        model=Device,
        required=False
    )

    solution = ChoiceVar(
        description="Choose the solution (e.g., EoIP, L2TP)",
        choices=[('EoIP', 'EoIP'), ('L2TP', 'L2TP'), ('OtherSolution', 'Other Solution')],
        required=True
    )

    # EoIP-specific variables
    eoip_wan_interface = ObjectVar(
        description="Select the WAN interface for EoIP",
        model=Interface,
        required=False
    )

    eoip_wan_ip = StringVar(
        description="Enter the WAN IP address for the EoIP interface",
        required=False
    )

    # L2TP-specific variables
    manual_ip = StringVar(
        description="Enter the IP in the format 192.168.2.1/30",
        required=False
    )

    pop_manual_ip = StringVar(
        description="Enter the IP for L2TP on the POP in the format 192.168.2.2/30",
        required=False
    )

    vlan_id = IntegerVar(
        description="Enter the VLAN ID",
        required=False
    )

    serial_number = StringVar(
        description="Enter the device's serial number (optional)",
        required=False
    )

    def run(self, data, commit):
        device = data['device']
        pop_device = data.get('pop_device')
        solution = data['solution']
        manual_ip = data.get('manual_ip')
        pop_manual_ip = data.get('pop_manual_ip')
        vlan_id = data.get('vlan_id')
        serial_number = data.get('serial_number')
        eoip_wan_interface = data.get('eoip_wan_interface')
        eoip_wan_ip = data.get('eoip_wan_ip')

        site = device.site
        pop_site = pop_device.site if pop_device else None

        self.log_info(f"Device: {device}, POP: {pop_device}, Site: {site.name}, POP Site: {pop_site.name if pop_site else 'N/A'}, Solution: {solution}, WAN Interface for EoIP: {eoip_wan_interface}, WAN IP for EoIP: {eoip_wan_ip}, IP: {manual_ip}, POP IP: {pop_manual_ip}, VLAN ID: {vlan_id}")

        # Function to create VLAN if it does not exist
        def get_or_create_vlan(vlan_id, site):
            vlan = VLAN.objects.filter(id=vlan_id).first()
            if not vlan:
                vlan = VLAN(
                    id=vlan_id,
                    name=f"VLAN {vlan_id}",
                    site=site,
                    vid=vlan_id
                )
                if commit:
                    try:
                        vlan.save()
                        self.log_success(f"VLAN '{vlan.name}' created and associated with site '{site.name}'.")
                    except Exception as e:
                        self.log_failure(f"Failed to create VLAN: {str(e)}")
                else:
                    self.log_info(f"Simulation: VLAN '{vlan.name}' would be created and associated with site '{site.name}'.")
            return vlan

        # Function to create interfaces on a specific device
        def create_interface(device, interface_name, ip=None, vlan=None):
            existing_interface = Interface.objects.filter(device=device, name=interface_name).first()
            if existing_interface:
                self.log_failure(f"Interface '{interface_name}' already exists on device '{device.name}'.")
            else:
                interface = Interface(
                    device=device,
                    name=interface_name,
                    type='virtual',
                    enabled=True
                )
                if commit:
                    try:
                        interface.save()
                        self.log_success(f"Interface '{interface_name}' successfully created on device '{device.name}'.")

                        # Associate IP with the interface
                        if ip:
                            ip_address = IPAddress(
                                address=ip,
                                assigned_object=interface,
                                assigned_object_type=ContentType.objects.get_for_model(interface)
                            )
                            ip_address.save()
                            self.log_success(f"IP '{ip_address.address}' successfully created and associated with interface '{interface_name}'.")

                        # Set the IP as primary if necessary
                        if ip:
                            device.primary_ip4 = ip_address
                            device.save()
                            self.log_success(f"IP '{ip_address.address}' set as primary for device '{device.name}'.")

                        # Associate VLAN with the interface
                        if vlan:
                            interface.vlan = vlan
                            interface.save()
                            self.log_success(f"VLAN '{vlan.name}' associated with interface '{interface_name}'.")

                    except Exception as e:
                        self.log_failure(f"Failed to create interface '{interface_name}': {str(e)}")
                else:
                    self.log_info(f"Simulation: Interface '{interface_name}' would be created on device '{device.name}'.")

        # Create or get the VLAN
        vlan = get_or_create_vlan(vlan_id, site)

        if solution == "EoIP":
            if eoip_wan_interface and eoip_wan_ip:
                # Create EoIP interface on the primary device with specified WAN IP
                create_interface(device, f"EoIP-{site.name}", eoip_wan_ip)

                # Create GRE interface on the primary device
                create_interface(device, f"GRE-{site.name}", manual_ip, vlan)

                # Create EoIP and GRE interfaces on the POP device, if provided
                if pop_device:
                    create_interface(pop_device, f"EoIP-{site.name}")
                    create_interface(pop_device, f"GRE-{site.name}", pop_manual_ip, vlan)
            else:
                self.log_failure("For EoIP, you must select a WAN interface and provide a WAN IP.")

        elif solution == "L2TP":
            # Create L2TP interface on the primary device
            create_interface(device, f"L2TP-{site.name}.A001", manual_ip, vlan)

            # Create L2TP interface on the POP device, if provided
            if pop_device:
                create_interface(pop_device, f"L2TP-{site.name}.A001", pop_manual_ip, vlan)

        # Set the serial number manually, if provided
        if serial_number:
            device.serial = serial_number
            device.save()
            self.log_success(f"Serial number '{serial_number}' set for device '{device.name}'.")

        # Check and log the serial number of the device
        if not device.serial:
            self.log_info("Device does not have a registered serial number.")

        return f"Process completed for devices {device.name} and {pop_device.name if pop_device else ''}."
